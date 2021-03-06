
CREATE TABLE public.boundary (
                boundary_id INTEGER NOT NULL,
                boundary_name VARCHAR(255) NOT NULL,
                boundary geometry(polygon) NOT NULL,
                creation_time TIMESTAMP NOT NULL,
                CONSTRAINT boundary_pk PRIMARY KEY (boundary_id)
);

CREATE UNIQUE INDEX boundary_idx
 ON public.boundary
 ( boundary_name );

CREATE TABLE public.parameter_type (
                parameter_type_id INTEGER NOT NULL,
                parameter_type_name VARCHAR(50) NOT NULL,
                parameter_location VARCHAR(50) NOT NULL,
                CONSTRAINT parameter_type_pk PRIMARY KEY (parameter_type_id)
);


CREATE UNIQUE INDEX parameter_type_idx
 ON public.parameter_type
 ( parameter_type_name );

CREATE TABLE public.parameter (
                parameter_id INTEGER NOT NULL,
                parameter_type_id INTEGER NOT NULL,
                parameter_name VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                CONSTRAINT parameter_pk PRIMARY KEY (parameter_id)
);


CREATE UNIQUE INDEX parameter_idx
 ON public.parameter
 ( parameter_name );

CREATE TABLE public.tag (
                tag_id INTEGER NOT NULL,
                tag VARCHAR(255) NOT NULL,
                CONSTRAINT tag_pk PRIMARY KEY (tag_id)
);


CREATE UNIQUE INDEX tag_idx
 ON public.tag
 ( tag );

CREATE TABLE public.file_format (
                file_format_id INTEGER NOT NULL,
                file_format_name VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                CONSTRAINT file_format_pk PRIMARY KEY (file_format_id)
);


CREATE UNIQUE INDEX file_format_idx
 ON public.file_format
 ( file_format_name );

CREATE TABLE public.file_type (
                file_type_id INTEGER NOT NULL,
                file_type_name VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                CONSTRAINT file_type_pk PRIMARY KEY (file_type_id)
);


CREATE UNIQUE INDEX file_type_idx
 ON public.file_type
 ( file_type_name );

CREATE TABLE public.file_type_parameter (
                file_type_id INTEGER NOT NULL,
                parameter_id INTEGER NOT NULL,
                CONSTRAINT file_type_parameter_pk PRIMARY KEY (file_type_id, parameter_id)
);


CREATE TABLE public.file (
                uid VARCHAR(255) NOT NULL,
                file_type_id INTEGER NOT NULL,
                file_format_id INTEGER NOT NULL,
                is_archived BOOLEAN NOT NULL,
                creation_time TIMESTAMP NOT NULL,
                CONSTRAINT file_pk PRIMARY KEY (uid)
);


CREATE INDEX file_idx
 ON public.file
 ( file_type_id, file_format_id );

CREATE TABLE public.file_uri (
                uid VARCHAR(255) NOT NULL,
                uri VARCHAR(255) NOT NULL,
                CONSTRAINT file_uri_pk PRIMARY KEY (uid, uri)
);


CREATE TABLE public.data_boundary (
                uid VARCHAR(255) NOT NULL,
                boundary_id INTEGER NOT NULL,
                CONSTRAINT data_boundary_pk PRIMARY KEY (uid)
);


CREATE TABLE public.parameter_linestring (
                uid VARCHAR(255) NOT NULL,
                parameter_id INTEGER NOT NULL,
                data_value geography(linestring) NOT NULL,
                creation_time TIMESTAMP NOT NULL,
                CONSTRAINT parameter_linestring_pk PRIMARY KEY (uid, parameter_id)
);


CREATE TABLE public.parameter_value (
                uid VARCHAR(255) NOT NULL,
                parameter_id INTEGER NOT NULL,
                data_value VARCHAR(3000) NOT NULL,
                creation_time TIMESTAMP NOT NULL,
                CONSTRAINT parameter_value_pk PRIMARY KEY (uid, parameter_id)
);


CREATE TABLE public.file_tag (
                tag_id INTEGER NOT NULL,
                uid VARCHAR(255) NOT NULL,
                CONSTRAINT file_tag_pk PRIMARY KEY (tag_id, uid)
);


CREATE TABLE public.file_access_uri (
                file_type_id INTEGER NOT NULL,
                file_format_id INTEGER NOT NULL,
                sequence INTEGER DEFAULT 1 NOT NULL,
                uri VARCHAR(255) NOT NULL,
                CONSTRAINT file_access_uri_pk PRIMARY KEY (file_type_id, file_format_id, sequence)
);


CREATE TABLE public.file_type_tag (
                tag_id INTEGER NOT NULL,
                file_type_id INTEGER NOT NULL,
                CONSTRAINT file_type_tag_pk PRIMARY KEY (tag_id, file_type_id)
);


ALTER TABLE public.data_boundary ADD CONSTRAINT boundary_data_boundary_fk
FOREIGN KEY (boundary_id)
REFERENCES public.boundary (boundary_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.parameter ADD CONSTRAINT parameter_type_parameter_fk
FOREIGN KEY (parameter_type_id)
REFERENCES public.parameter_type (parameter_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.parameter_value ADD CONSTRAINT parameter_parameter_value_fk
FOREIGN KEY (parameter_id)
REFERENCES public.parameter (parameter_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.parameter_linestring ADD CONSTRAINT parameter_parameter_track_fk
FOREIGN KEY (parameter_id)
REFERENCES public.parameter (parameter_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_type_parameter ADD CONSTRAINT parameter_file_type_parameter_fk
FOREIGN KEY (parameter_id)
REFERENCES public.parameter (parameter_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_type_tag ADD CONSTRAINT tag_file_type_tag_fk
FOREIGN KEY (tag_id)
REFERENCES public.tag (tag_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_tag ADD CONSTRAINT tag_file_tag_fk
FOREIGN KEY (tag_id)
REFERENCES public.tag (tag_id)
ON DELETE CASCADE
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_access_uri ADD CONSTRAINT file_format_file_uri_fk
FOREIGN KEY (file_format_id)
REFERENCES public.file_format (file_format_id)
ON DELETE CASCADE
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file ADD CONSTRAINT file_format_file_fk
FOREIGN KEY (file_format_id)
REFERENCES public.file_format (file_format_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_type_tag ADD CONSTRAINT file_type_file_type_tag_fk
FOREIGN KEY (file_type_id)
REFERENCES public.file_type (file_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_access_uri ADD CONSTRAINT file_type_file_uri_fk
FOREIGN KEY (file_type_id)
REFERENCES public.file_type (file_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file ADD CONSTRAINT file_type_file_fk
FOREIGN KEY (file_type_id)
REFERENCES public.file_type (file_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_type_parameter ADD CONSTRAINT file_type_file_type_parameter_fk
FOREIGN KEY (file_type_id)
REFERENCES public.file_type (file_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_tag ADD CONSTRAINT file_file_tag_fk
FOREIGN KEY (uid)
REFERENCES public.file (uid)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.parameter_value ADD CONSTRAINT file_parameter_value_fk
FOREIGN KEY (uid)
REFERENCES public.file (uid)
ON DELETE CASCADE
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.parameter_linestring ADD CONSTRAINT file_parameter_track_fk
FOREIGN KEY (uid)
REFERENCES public.file (uid)
ON DELETE CASCADE
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.data_boundary ADD CONSTRAINT file_data_boundary_fk
FOREIGN KEY (uid)
REFERENCES public.file (uid)
ON DELETE CASCADE
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.file_uri ADD CONSTRAINT file_file_uri_fk
FOREIGN KEY (uid)
REFERENCES public.file (uid)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

CREATE INDEX track_gix ON parameter_linestring USING GIST (data_value);
CREATE INDEX boundary_gix ON boundary USING GIST (boundary);

