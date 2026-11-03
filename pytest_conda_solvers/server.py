import mimetypes
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from fastapi_cache import Coder, FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from pytest import fixture

from .data import get_channel_repodata, load_raw_data_file


class RepodataFilename(str, Enum):
    repodata = "repodata.json"
    current_repodata = "current_repodata.json"


class ChannelServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_base_url(self, add_pip=False, features_as_track_features=False):
        # Each served variant of the index lives under its own path prefix, so
        # the variants never share conda's repodata caches, which are keyed by
        # URL. The prefixes compose in a fixed order, see the routes below.
        segments = [f"http://{self.host}:{self.port}"]
        if add_pip:
            segments.append("with-pip")
        if features_as_track_features:
            segments.append("track-features")
        return "/".join(segments)

    def get_channel_url(self, channel, add_pip=False, features_as_track_features=False):
        return f"{self.get_base_url(add_pip, features_as_track_features)}/{channel}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


class NullCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return value

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return value


@fixture(scope="session")
def channel_server(host="localhost", port=8080):
    app = FastAPI(lifespan=lifespan)

    # The conda-format repo is a static copy of upstream's
    # tests/data/conda_format_repo, served file by file. It is reachable under
    # every index-variant prefix below, unchanged, so that an entry can combine
    # it with the generated channels under a single base URL.
    @app.get("/conda_format_repo/{full_path:path}")
    @app.get("/with-pip/conda_format_repo/{full_path:path}")
    @app.get("/track-features/conda_format_repo/{full_path:path}")
    @app.get("/with-pip/track-features/conda_format_repo/{full_path:path}")
    @cache(coder=NullCoder)
    async def conda_format_repo_contents(full_path: str):
        path = Path(f"conda_format_repo/{full_path}")
        try:
            data = load_raw_data_file(path)
        except FileNotFoundError:
            # Missing variants such as current_repodata.json.zst raise a 404,
            # to make conda fall back to the uncompressed filename instead of
            # treating the fetch as a server failure
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        mimetype = mimetypes.guess_type(path)[0]
        return Response(data, media_type=mimetype)

    def serve_repodata(channel_name: str, subdir: str, filename: str, **variant):
        # Validate the filename manually and return 404 for unsupported repodata
        # variants rather than relying on FastAPI's enum validation (which returns
        # 422). This server only serves repodata.json and current_repodata.json.
        # Compressed and sharded repodata variants, such as repodata.json.zst or
        # repodata_shards.msgpack.zst are not available, and a 404 tells libmamba
        # to fall back to repodata.json.
        try:
            validated = RepodataFilename(filename)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return get_channel_repodata(channel_name, subdir, validated.value, **variant)

    # The routes below serve the same channels under distinct path prefixes,
    # one per combination of the index variants ChannelServer.get_base_url
    # composes. They are separate functions, since the response cache is
    # keyed by function name and path parameters.

    @app.get("/with-pip/{channel_name}/{subdir}/{filename}")
    @cache()
    async def pip_injected_repodata(
        channel_name: str,
        subdir: str,
        filename: str,
    ):
        # Serve the same repodata with 'pip' appended to the depends of every
        # python 2.x/3.x record, mirroring conda's SubdirData injection under
        # add_pip_as_python_dependency. Upstream's test fixtures bake pip into
        # the served index data this way, and serving it here makes the
        # injection visible to solvers that read repodata directly, such as
        # rattler, instead of relying on conda's SubdirData at solve time.
        # TODO: this route can be removed once conda-rattler-solver honours the
        # setting, see https://github.com/conda/conda-rattler-solver/issues/122
        return serve_repodata(channel_name, subdir, filename, add_pip=True)

    @app.get("/track-features/{channel_name}/{subdir}/{filename}")
    @cache()
    async def track_features_repodata(
        channel_name: str,
        subdir: str,
        filename: str,
    ):
        # Serve the index as upstream exports it to disk for the non-classic
        # solvers, with every record's 'features' exposed as 'track_features'.
        # Only the channels converted from upstream's index fixtures are
        # rewritten, see EXPORTED_CHANNELS in pytest_conda_solvers.data.
        return serve_repodata(
            channel_name, subdir, filename, features_as_track_features=True
        )

    @app.get("/with-pip/track-features/{channel_name}/{subdir}/{filename}")
    @cache()
    async def pip_injected_track_features_repodata(
        channel_name: str,
        subdir: str,
        filename: str,
    ):
        return serve_repodata(
            channel_name,
            subdir,
            filename,
            add_pip=True,
            features_as_track_features=True,
        )

    @app.get("/{channel_name}/{subdir}/{filename}")
    @cache()
    async def repodata(
        channel_name: str,
        subdir: str,
        filename: str,
    ):
        return serve_repodata(channel_name, subdir, filename)

    @app.get("/{full_path:path}")
    async def catch_all():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={
            "host": host,
            "port": port,
        },
        daemon=True,
    )
    thread.start()

    yield ChannelServer(host, port)
