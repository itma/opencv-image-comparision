# opencv-image-comparision
A simple OpenCV implementation to perform image comparison at a scale.

The image comparison mainly bases on the OpenCV histograms matching method which is used to prefilter and narrow the results for the further processing by the structural_similarity method imported from skimage.metrics. Overall, the approach works well if images being compared are of the same source, and does not work well enough for the scenario like a comparison of a book cover taken by a mobile camera against a set of book covers downloaded from the net.

### Histograms - inital import ###

```
# To build the db data structure use the file https://github.com/itma/opencv-image-comparision/blob/main/db_schema.sql
databaseConnection = psycopg2.connect(
    host="localhost",
    database="db_name",
    user="db_user",
    password="db_password")

# MULTIPLE MATCHING TEST
imageRecognizer = ImageRecognition()
imageRecognizer.setDatabaseConnection(databaseConnection)
# Right now only 2 is supported
imageRecognizer.setHistogramType(2)
# The path to the query images set
# Call it once you train the histogram set, then don't call again
imageRecognizer.setTrainingPath('/home/app/covers')
# Call it once you train the histogram set, then don't call again
imageRecognizer.insertHistograms()
```

### Comparision (multiple images) ###

```
# To build the db data structure use the file https://github.com/itma/opencv-image-comparision/blob/main/db_schema.sql
databaseConnection = psycopg2.connect(
    host="localhost",
    database="db_name",
    user="db_user",
    password="db_password")

# MULTIPLE MATCHING
imageRecognizer = ImageRecognition()
imageRecognizer.setDatabaseConnection(databaseConnection)
# Right now only 2 is supported
imageRecognizer.setHistogramType(2)
# The path to the query images set
imageRecognizer.setQueryPath('/home/app/query')
bestMatchFilename = imageRecognizer.predictByMultiple()
print(bestMatchFilename)
```

### Comparision (single image) ###

```
# To build the db data structure use the file https://github.com/itma/opencv-image-comparision/blob/main/db_schema.sql
databaseConnection = psycopg2.connect(
    host="localhost",
    database="db_name",
    user="db_user",
    password="db_password")

# MULTIPLE MATCHING
imageRecognizer = ImageRecognition()
imageRecognizer.setDatabaseConnection(databaseConnection)
# Right now only 2 is supported
imageRecognizer.setHistogramType(2)
# The path to the query image
imageRecognizer.setQueryImage('/home/app/query/search_for_that_image.jpg')
bestMatchFilename = imageRecognizer.predictBySingle()
print(bestMatchFilename)
```
