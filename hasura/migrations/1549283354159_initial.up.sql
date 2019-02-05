


CREATE TABLE public.user
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  email text NOT NULL,
  active boolean NOT NULL DEFAULT false,
  created timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT user_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.user
  OWNER TO postgres;


CREATE TABLE public.project
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  contact text NOT NULL,
  CONSTRAINT project_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.project
  OWNER TO postgres;


CREATE TABLE public.parameter
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  value text NOT NULL,
  param_type text NOT NULL,
  CONSTRAINT parameter_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.parameter
  OWNER TO postgres;


CREATE TABLE public.user_project
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  project_id uuid,
  CONSTRAINT user_project_pkey PRIMARY KEY (id),
  CONSTRAINT user_project_project_id_fkey FOREIGN KEY (project_id)
      REFERENCES public.project (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT user_project_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES public.user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.user_project
  OWNER TO postgres;


CREATE TABLE public.repository
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  url text NOT NULL,
  username text NOT NULL,
  password text NOT NULL,
  user_id uuid,
  CONSTRAINT repository_pkey PRIMARY KEY (id),
  CONSTRAINT repository_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES public.user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.repository
  OWNER TO postgres;


CREATE TABLE public.configuration_type
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text NOT NULL,
  CONSTRAINT types_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.configuration_type
  OWNER TO postgres;


CREATE TABLE public.configuration
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  repository_id uuid NOT NULL,
  project_id uuid NOT NULL,
  type_id uuid,
  CONSTRAINT configuration_pkey PRIMARY KEY (id),
  CONSTRAINT configuration_project_id_fkey FOREIGN KEY (project_id)
      REFERENCES public.project (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT configuration_repository_id_fkey FOREIGN KEY (repository_id)
      REFERENCES public.repository (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT configuration_type_id_fkey FOREIGN KEY (type_id)
      REFERENCES public.configuration_type (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.configuration
  OWNER TO postgres;


CREATE TABLE public.execution
(
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  configuration_id uuid NOT NULL,
  start timestamp with time zone,
  "end" timestamp with time zone,
  status text NOT NULL,
  CONSTRAINT execution_pkey PRIMARY KEY (id),
  CONSTRAINT execution_configuration_id_fkey FOREIGN KEY (configuration_id)
      REFERENCES public.configuration (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.execution
  OWNER TO postgres;
