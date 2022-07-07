import os
import cv2
import debugpy
import pickle
import numpy as np
import glob
import pandas as pd
from skimage.metrics import structural_similarity
import psycopg2
import hashlib
import time

#debugpy.listen(("0.0.0.0", 5678))
#print("Waiting for client to attach...")
# debugpy.wait_for_client()

"""
ImageRecognition class provides the way to find the best matches for a given
query image.

@author Andrzej Bernat <andrzej@itma.pl>
"""


class ImageRecognition:

    queryPath = None
    queryImage = None
    trainingPath = None
    flannInstance = None
    bestMatch = None

    histogramType = []
    histogramSize = []
    histogramRange = []

    databaseConnection = None
    databaseCursor = None

    predictions = []
    trainedHistograms = []
    queryHistograms = []
    matchedByHistograms = []
    matchedBySimilarity = []

    # Parameter for comparing histograms
    SIMILARITY_CORRELATION_THRESHOLD = 0.9
    SIMILARITY_INDEX_THRESHOLD = 0.0
    SIMILARITY_MATCHES_LIMIT = 1000

    # Parameters for SIFT comparision
    SIFT_FEATURES_LIMIT = 1000
    SIFT_LOWE_RATIO = 0.75
    SIFT_PREDICTIONS_AMOUNT = 1

    # FLANN matcher
    FLANN_INDEX_KDTREE = 0
    flannInstanceIndexParams = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    flannInstanceSearchParams = dict(checks=50)   # or pass empty dictionary

    def __init__(self) -> None:
        self.flannInstance = cv2.FlannBasedMatcher(
            self.flannInstanceIndexParams,
            self.flannInstanceSearchParams
        )

    def setHistogramType(self, type) -> None:
        if type == 0:
            self.histogramType = [0]
            self.histogramSize = [8]
            self.histogramRange = [0, 256]
        if type == 1:
            self.histogramType = [0, 1]
            self.histogramSize = [8, 8]
            self.histogramRange = [0, 256, 0, 256]
        if type == 2:
            self.histogramType = [0, 1, 2]
            self.histogramSize = [8, 8, 8]
            self.histogramRange = [0, 256, 0, 256, 0, 256]

    def setDatabaseConnection(self, databaseConnection):
        self.databaseConnection = databaseConnection
        # create a cursor
        self.databaseCursor = self.databaseConnection.cursor()

    def setQueryPath(self, path):
        """
        Set the path to the quering image set
        """
        self.queryPath = path

    def setQueryImage(self, path):
        """
        Set the path to the quering single image
        """
        self.queryImage = path

    def setTrainingPath(self, path):
        """
        Set the path to the traing set
        """
        self.trainingPath = path

    def getImages(self, path):
        """
        The function getImages returns all the names of the files in 
        the directory path supplied as argument to the function.
        """
        return [os.path.join(path, f) for f in os.listdir(path)]

    def insertHistograms(self):
        """
        Build a histogram list for the given trainging set
        """
        trainingPaths = []
        for root, dirs, files in os.walk(self.trainingPath):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg')):
                    trainingPaths.append((os.path.join(root, file)))

        for path in trainingPaths:
            image = cv2.imread(path)
            if image is None:
                continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # extract a 3D RGB color histogram from the image,
            # using 8 bins per channel, normalize, and update
            # the index
            hist = cv2.calcHist([image], self.histogramType,
                                None, self.histogramSize, self.histogramRange)
            hist = cv2.normalize(hist, None)

            # todo: This is going to be a db record
            # path =
            #self.databaseCursor.execute('SELECT * FROM image_histogram')
            self.databaseCursor.execute('INSERT INTO image_histogram (path, histogram, created_at, image_source_id, type) VALUES (%s, %s, %s, %s, %s)',
                                        (path, pickle.dumps(hist),
                                         int(time.time()), 1, 0)
                                        )
            self.databaseConnection.commit()

        return pickle.TRUE

    def loadHistograms(self):
        """
        Loading the train data histograms
        """

        self.databaseCursor.execute(
            "SELECT * FROM image_histogram WHERE image_source_id = 1'")
        rows = self.databaseCursor.fetchall()

        for row in rows:
            self.trainedHistograms.append((row[1], pickle.loads(row[3])))

        return self.trainedHistograms

    def getQueryHistogramByMultipleImages(self):
        """
        Fetch histogram for the query images set
        """
        for path in self.getImages(self.queryPath):
            if path.lower().endswith(('.jpg', '.jpeg')):
                image = cv2.imread(path)
                if image is None:
                    continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # extract a 3D RGB color histogram from the image,
            # using 8 bins per channel, normalize, and update the index
            histogram = cv2.calcHist(
                [image], self.histogramType, None, self.histogramSize, self.histogramRange)
            histogram = cv2.normalize(histogram, None)
            self.queryHistograms.append((path, histogram))

        return self.queryHistograms

    def getQueryHistogramBySingleImage(self):
        """
        Fetch histogram for the query images set
        """
        image = cv2.imread(self.queryImage)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # extract a 3D RGB color histogram from the image,
        # using 8 bins per channel, normalize, and update the index
        hist = cv2.calcHist([image], self.histogramType,
                            None, self.histogramSize, self.histogramRange)
        hist = cv2.normalize(hist, None)
        self.queryHistograms.append((self.queryImage, hist))

        return self.queryHistograms

    def matchHistogramsByMiltipleQueries(self):
        """
        Match query histogram against cached histograms
        """
        for i in range(len(self.queryHistograms)):
            matches = []
            for j in range(len(self.trainedHistograms)):
                cmp = cv2.compareHist(
                    self.queryHistograms[i][1], self.trainedHistograms[j][1], cv2.HISTCMP_CORREL)
                if cmp > self.SIMILARITY_CORRELATION_THRESHOLD:
                    matches.append((cmp, self.trainedHistograms[j][0]))
            matches.sort(key=lambda x: x[0], reverse=True)
            self.matchedByHistograms.append(
                (self.queryHistograms[i][0], matches))

        for i in range(len(self.matchedByHistograms)):
            q_text = self.matchedByHistograms[i][0].split("/")[-1]
            p_text = []
            for j in range(len(self.matchedByHistograms[i][1])):
                text = self.matchedByHistograms[i][1][j][1].split("/")[-1]
                p_text.append(text)

        return self.matchedByHistograms

    def matchHistogramsBySingleQuery(self):
        """
        Match query histogram against cached histograms
        """
        matches = []
        for j in range(len(self.trainedHistograms)):
            cmp = cv2.compareHist(
                self.queryHistograms[0][1], self.trainedHistograms[j][1], cv2.HISTCMP_CORREL)
            if cmp > self.SIMILARITY_CORRELATION_THRESHOLD:
                matches.append((cmp, self.trainedHistograms[j][0]))

        matches.sort(key=lambda x: x[0], reverse=True)

        self.matchedByHistograms.append(
            (self.queryHistograms[0][0], matches))

        for i in range(len(self.matchedByHistograms)):
            q_text = self.matchedByHistograms[i][0].split("/")[-1]
            p_text = []
            for j in range(len(self.matchedByHistograms[i][1])):
                text = self.matchedByHistograms[i][1][j][1].split("/")[-1]
                p_text.append(text)

        return self.matchedByHistograms

    def similarityIndex(self, queryPath, trainingPath):
        queryImageMatrix = cv2.imread(queryPath, 0)
        queryImageResized = cv2.resize(queryImageMatrix, (8, 8))
        trainingImageMatrix = cv2.imread(trainingPath, 0)
        trainingImageResized = cv2.resize(trainingImageMatrix, (8, 8))
        return structural_similarity(queryImageResized, trainingImageResized)

    def matchNarrowedHistogramsByMiltipleQueries(self) -> list:
        """

        """
        for i in range(len(self.matchedByHistograms)):
            queryPath = self.matchedByHistograms[i][0]
            matches = []
            for j in range(len(self.matchedByHistograms[i][1])):
                trainingPath = self.matchedByHistograms[i][1][j][1]
                si = self.similarityIndex(queryPath, trainingPath)
                if si > self.SIMILARITY_INDEX_THRESHOLD:
                    matches.append((si, trainingPath))

            matches.sort(key=lambda x: x[0], reverse=True)
            self.matchedBySimilarity.append(
                (queryPath, matches[:self.SIMILARITY_MATCHES_LIMIT])
            )

        return self.matchedBySimilarity

    def matchNarrowedHistogramsBySingleQuery(self) -> list:
        """

        """
        for i in range(len(self.matchedByHistograms)):
            queryPath = self.matchedByHistograms[i][0]
            matches = []
            for j in range(len(self.matchedByHistograms[i][1])):
                trainingPath = self.matchedByHistograms[i][1][j][1]
                si = self.similarityIndex(queryPath, trainingPath)
                if si > self.SIMILARITY_INDEX_THRESHOLD:
                    matches.append((si, trainingPath))

            matches.sort(key=lambda x: x[0], reverse=True)
            self.matchedBySimilarity.append(
                (queryPath, matches[:self.SIMILARITY_MATCHES_LIMIT])
            )

        return self.matchedBySimilarity

    def createSiftFeatures(self, image):
        """

        """
        sift = cv2.xfeatures2d.SIFT_create(self.SIFT_FEATURES_LIMIT)
        # desc is the SIFT descriptors, they're 128-dimensional vectors
        # that we can use for our final features
        kp, desc = sift.detectAndCompute(image, None)
        return desc

    def predictByMultiple(self) -> str:
        """
        Makes a prediction for the best match for the given query
        """
        self.loadHistograms()
        self.getQueryHistogramByMultipleImages()
        self.matchHistogramsByMiltipleQueries()
        self.matchNarrowedHistogramsByMiltipleQueries()
        return self.getBestMatch()

    def predictBySingle(self) -> str:
        """
        Makes a prediction for the best match for the given query
        """
        self.loadHistograms()
        self.getQueryHistogramBySingleImage()
        self.matchHistogramsBySingleQuery()
        self.matchNarrowedHistogramsBySingleQuery()
        return self.getBestMatch()

    def getBestMatch(self) -> str:
        """
        Returns the best fit for the given query
        """
        for i in range(len(self.matchedBySimilarity)):
            matches_flann = []
            # Reading query image
            queryPath = self.matchedBySimilarity[i][0]
            queryImageMatrix = cv2.imread(queryPath)
            if queryImageMatrix is None:
                continue
            queryImageConverted = cv2.cvtColor(
                queryImageMatrix, cv2.COLOR_BGR2RGB)
            # Generating SIFT features for query image
            q_des = self.createSiftFeatures(queryImageConverted)
            if q_des is None:
                continue

            for j in range(len(self.matchedBySimilarity[i][1])):

                matchesCounter = 0

                m_path = self.matchedBySimilarity[i][1][j][1]
                m_img = cv2.imread(m_path)
                if m_img is None:
                    continue

                m_img = cv2.cvtColor(m_img, cv2.COLOR_BGR2RGB)

                # Generating SIFT features for predicted ssim images
                m_des = self.createSiftFeatures(m_img)
                if m_des is None:
                    continue

                # Calculating number of feature matches using FLANN
                try:
                    matches = self.flannInstance.knnMatch(q_des, m_des, k=2)
                except BaseException:
                    continue

                # ratio query as per Lowe's paper
                matchesCounter = 0
                for x, (m, n) in enumerate(matches):
                    if m.distance < self.SIFT_LOWE_RATIO*n.distance:
                        matchesCounter += 1

                matches_flann.append((matchesCounter, m_path))

            matches_flann.sort(key=lambda x: x[0], reverse=True)
            self.predictions.append(
                (queryPath, matches_flann[:self.SIFT_PREDICTIONS_AMOUNT]))

        self.predictions.sort(key=lambda x: x[0], reverse=True)
        return self.predictions

    def getItem(self) -> str:
        # Prepare the best match result format
        bestMatch = None
        if len(self.predictions) > 0:
            if len(self.predictions[0]) > 0:
                bestMatch = self.predictions[0][0]
                bestMatch = os.path.basename(bestMatch)

        # Return the filename without type. The name can be anything (product id etc..)
        return bestMatch.split('.')[0]
