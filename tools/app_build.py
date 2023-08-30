import PyInstaller.__main__
from project_directory import ProjectDirectory


def main():
    pd = ProjectDirectory()

    PyInstaller.__main__.run(
        [str(pd.main_script_path), "--onefile", "--icon", str(pd.icon_path)]
    )


if __name__ == "__main__":
    main()
