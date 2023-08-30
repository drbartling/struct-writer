# pylint: disable=fixme

import os
import subprocess
import uuid

import app_build
import click
import pkg_resources
from project_directory import ProjectDirectory


@click.command()
def main():
    pd = ProjectDirectory()
    dist = pkg_resources.get_distribution("hello")

    app_build.main()
    pd.build_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(pd.build_dir)

    subprocess.run(
        " ".join(
            [
                "candle.exe",
                str(pd.wxs_path),
                '-dcompany_name="Acme Co"',
                '-dproduct_name="hello"',
                f'-dupgrade_code="{uuid.uuid4()}"',  # TODO: Hard code a permanent uuid
                f'-dpath_code="{uuid.uuid4()}"',  # TODO: Hard code a permanent uuid
                f'-dproduct_version="{dist.version}"',
                '-ddescription="Hello Greeter Application"',
                f'-dlicense_file="{pd.license_path}"',
                f'-dicon_path="{pd.icon_path}"',
                f'-dexecutable_path="{pd.executable_path}"',
                f'-dexecutable_name="{pd.executable_path.name}"',
            ]
        ),
        capture_output=False,
        check=True,
    )

    subprocess.run(
        " ".join(
            [
                "light.exe",
                f'-out "{pd.msi_path}"',
                "hello.wixobj",
                "-cultures:en-US",
                "-ext WixUIExtension",  # Adds installer GUI support
            ]
        ),
        capture_output=False,
        check=True,
    )


if __name__ == "__main__":
    main()
