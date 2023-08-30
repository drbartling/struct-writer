from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectDirectory:
    @property
    def script_dir(self) -> Path:
        script_dir = Path(__file__).parent
        assert script_dir.is_dir()
        return script_dir

    @property
    def wxs_path(self) -> Path:
        wxs_path = self.script_dir / "hello.wxs"
        assert wxs_path.is_file()
        return wxs_path

    @property
    def icon_path(self) -> Path:
        icon_path = self.script_dir / "icon.ico"
        assert icon_path.is_file()
        return icon_path

    @property
    def root_dir(self) -> Path:
        root_dir = self.script_dir.parent
        assert root_dir.is_dir()
        return root_dir

    @property
    def license_path(self) -> Path:
        license_path = self.root_dir / "license.rtf"
        assert license_path.is_file()
        return license_path

    @property
    def dist_dir(self) -> Path:
        dist_dir = self.root_dir / "dist"
        # Created during build, may not exist at start
        return dist_dir

    @property
    def executable_path(self) -> Path:
        executable_path = self.dist_dir / "hello.exe"
        # Created during build, may not exist at start
        return executable_path

    @property
    def msi_path(self) -> Path:
        msi_path = self.dist_dir / "hello.msi"
        assert msi_path.is_file()
        return msi_path

    @property
    def build_dir(self) -> Path:
        build_dir = self.root_dir / "build"
        # Created during build, may not exist at start
        return build_dir

    @property
    def src_dir(self) -> Path:
        src_dir = self.root_dir / "src"
        assert src_dir.is_dir()
        return src_dir

    @property
    def main_script_path(self) -> Path:
        main_script_path = self.src_dir / "hello/hello.py"
        assert main_script_path.is_file()
        return main_script_path
