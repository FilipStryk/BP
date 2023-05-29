-- Adminer 4.8.1 PostgreSQL 15.3 (Debian 15.3-1.pgdg110+1) dump

DROP TABLE IF EXISTS "points";
DROP SEQUENCE IF EXISTS points_id_seq;
CREATE SEQUENCE points_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 57354 CACHE 1;

CREATE TABLE "public"."points" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "track_id" uuid NOT NULL,
    "captured_at" timestamp(3) NOT NULL,
    "latitude" double precision NOT NULL,
    "longitude" double precision NOT NULL,
    "x" integer NOT NULL,
    "y" integer NOT NULL,
    "distance" real DEFAULT '0',
    "speed" real DEFAULT '0',
    CONSTRAINT "points_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "tracks";
CREATE TABLE "public"."tracks" (
    "id" uuid NOT NULL,
    "device_id" integer NOT NULL,
    "created_at" timestamp DEFAULT now() NOT NULL,
    "active" boolean DEFAULT true NOT NULL,
    CONSTRAINT "tracks_id" PRIMARY KEY ("id")
) WITH (oids = false);


ALTER TABLE ONLY "public"."points" ADD CONSTRAINT "points_track_id_fkey" FOREIGN KEY (track_id) REFERENCES tracks(id) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE;

-- 2023-05-26 22:04:34.635905+00