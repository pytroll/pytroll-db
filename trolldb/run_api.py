"""The main entry point to run the API server according to the configurations given in `config.yaml`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from api.api import run_server

if __name__ == "__main__":
    run_server("config.yaml")
