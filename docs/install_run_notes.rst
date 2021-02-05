T-Rex repository
****************

Contains
-----------

* S^n API services

    * API classes for providers, to query providers for S^n output
    * automated tests

* Specify resolver 

  * query IPT and specify colllection endpoints
  * read a DWCA into a CSV file for Solr input
  * 


Dependencies:
-------------
To be installed in lifemapper-core, the base roll with dependencies for this package

* Frontend and Testing

    * cherrypy==18.6.0
    * openapi-core== 0.13.5 (also openapi-spec-validator, pulled here)
      https://files.pythonhosted.org/packages/66/54/a0538d6a0e9553f33a5952d6ec750c361f10a7b37757dedb26dbe32b1582/openapi_core-0.13.5-py3-none-any.whl
    
        * six (from openapi-core==0.13.5) (1.15.0)
        * parse-1.19.0.tar.gz (30 kB)
        * openapi_schema_validator-0.1.1-py3-none-any.whl

            * jsonschema (from openapi-schema-validator->openapi-core==0.13.5) (3.2.0)

                * importlib-metadata; python_version < "3.8" (from jsonschema->openapi-schema-validator->openapi-core==0.13.5) (1.7.0)

                    * zipp>=0.5 (from importlib-metadata; python_version < "3.8"->jsonschema->openapi-schema-validator->openapi-core==0.13.5) (3.1.0)

                * setuptools (from jsonschema->openapi-schema-validator->openapi-core==0.13.5) (41.2.0)
                * pyrsistent>=0.14.0 (from jsonschema->openapi-schema-validator->openapi-core==0.13.5) (0.17.3)

        * more-itertools 
        * Werkzeug-1.0.1-py2.py3-none-any.whl
        * openapi-spec-validator 
        
            * PyYAML>=5.1 (from openapi-spec-validator->openapi-core==0.13.5) (5.4.1)
        
        * attrs (from openapi-core==0.13.5) (20.1.0)
        * lazy_object_proxy-1.5.2-cp36-cp36m-manylinux1_x86_64.whl (51 kB)
        * isodate-0.6.0-py2.py3-none-any.whl (45 kB)
        * strict-rfc3339-0.7.tar.gz (17 kB)

    * openapi3==1.1.0
      https://files.pythonhosted.org/packages/2b/92/6b843cb55829aacd917d6465381998b82a5cc2825fa5fc07b57fb0d65f96/openapi3-1.1.0-py2.py3-none-any.whl

        * PyYaml (from openapi3==1.1.0) (5.4.1)
        * requests (from openapi3==1.1.0) (2.24.0)

            * idna<3,>=2.5 (from requests->openapi3==1.1.0) (2.10)
            * certifi>=2017.4.17 (from requests->openapi3==1.1.0) (2020.6.20)
            * urllib3!=1.25.0,!=1.25.1,<1.26,>=1.21.1 (from requests->openapi3==1.1.0) (1.25.10)
            * chardet<4,>=3.0.2 (from requests->openapi3==1.1.0) (3.0.4)
        

    * simplejson==3.17.2
      https://pypi.org/project/simplejson/3.17.2/

    * Jinja2==2.11.3

        * MarkupSafe (1.1.1)

* Testing only

    * termcolor==1.1.0
      https://files.pythonhosted.org/packages/8a/48/a76be51647d0eb9f10e2a4511bf3ffb8cc1e6b14e9e4fab46173aa79f981/termcolor-1.1.0.tar.gz
    * dataclasses==0.8
      https://files.pythonhosted.org/packages/fe/ca/75fac5856ab5cfa51bbbcefa250182e50441074fdc3f803f6e76451fab43/dataclasses-0.8-py3-none-any.whl
      
