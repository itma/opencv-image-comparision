CREATE DATABASE ir
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

GRANT TEMPORARY, CONNECT ON DATABASE ir TO PUBLIC;

GRANT ALL ON DATABASE ir TO postgres;

GRANT ALL ON DATABASE ir TO ir;

-- SCHEMA: public

-- DROP SCHEMA public ;

CREATE SCHEMA public
    AUTHORIZATION postgres;

COMMENT ON SCHEMA public
    IS 'standard public schema';

GRANT ALL ON SCHEMA public TO PUBLIC;

GRANT ALL ON SCHEMA public TO postgres;

-- SEQUENCE: public.image_histogram_id_seq

-- DROP SEQUENCE public.image_histogram_id_seq;

CREATE SEQUENCE public.image_histogram_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE public.image_histogram_id_seq
    OWNER TO postgres;

GRANT ALL ON SEQUENCE public.image_histogram_id_seq TO ir;

GRANT ALL ON SEQUENCE public.image_histogram_id_seq TO postgres;


-- SEQUENCE: public.image_source_id_seq

-- DROP SEQUENCE public.image_source_id_seq;

CREATE SEQUENCE public.image_source_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE public.image_source_id_seq
    OWNER TO postgres;

-- Table: public.image_histogram

-- DROP TABLE public.image_histogram;

CREATE TABLE public.image_histogram
(
    id bigint NOT NULL DEFAULT nextval('image_histogram_id_seq'::regclass),
    path character varying(255) COLLATE pg_catalog."default" NOT NULL,
    created_at bigint,
    histogram bytea,
    image_source_id bigint NOT NULL,
    type integer NOT NULL DEFAULT 210,
    CONSTRAINT image_histogram_pkey PRIMARY KEY (id),
    CONSTRAINT image_source_id_fk_1 FOREIGN KEY (image_source_id)
        REFERENCES public.image_source (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.image_histogram
    OWNER to postgres;

GRANT ALL ON TABLE public.image_histogram TO ir;

GRANT ALL ON TABLE public.image_histogram TO postgres;
-- Index: fki_image_source_id_fk_1

-- DROP INDEX public.fki_image_source_id_fk_1;

CREATE INDEX fki_image_source_id_fk_1
    ON public.image_histogram USING btree
    (image_source_id ASC NULLS LAST)
    TABLESPACE pg_default;


-- Table: public.image_source

-- DROP TABLE public.image_source;

CREATE TABLE public.image_source
(
    id bigint NOT NULL DEFAULT nextval('image_source_id_seq'::regclass),
    source character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT image_source_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.image_source
    OWNER to postgres;
