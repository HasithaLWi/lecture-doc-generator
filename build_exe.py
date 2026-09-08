import os
import shutil
import sys
from pathlib import Path
import PyInstaller.__main__

def build():
    """Builds a standalone, single-file Windows executable for Lecture Document Generator."""
    project_root = Path(__file__).resolve().parent

    print("=" * 60)
    print(" BUILDING STANDALONE EXECUTABLE: LectureDocGenerator.exe")
    print("=" * 60)

    # 1. Clean previous builds
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    if build_dir.exists():
        print("[Build] Cleaning build directory...")
        shutil.rmtree(build_dir, ignore_errors=True)
    if dist_dir.exists():
        print("[Build] Cleaning previous dist directory...")
        for item in dist_dir.glob("LectureDocGenerator*"):
            if item.is_file():
                try:
                    item.unlink()
                except Exception:
                    pass

    # 2. Locate CustomTkinter directory for assets
    import customtkinter
    ctk_dir = Path(customtkinter.__file__).resolve().parent

    # 3. Configure PyInstaller Arguments
    entry_point = str(project_root / "gui.py")

    args = [
        entry_point,
        "--onefile",
        "--windowed",
        "--name=LectureDocGenerator",
        f"--add-data={ctk_dir};customtkinter",
        "--collect-data=customtkinter",
        "--collect-all=winocr",
        "--collect-all=pymupdf",
        "--collect-all=google.genai",
        "--hidden-import=PIL",
        "--hidden-import=docx",
        "--hidden-import=dotenv",
        "--hidden-import=winrt",
        "--hidden-import=winrt.windows.media.ocr",
        f"--workpath={project_root / 'build'}",
        f"--distpath={project_root / 'dist'}",
        f"--specpath={project_root / 'build'}",
        "--clean",
        "--noconfirm",
    ]

    print("[Build] Running PyInstaller with arguments:")
    for a in args:
        print(f"  {a}")
    print("\n[Build] Compiling... This may take 1-2 minutes...")

    PyInstaller.__main__.run(args)

    output_exe = dist_dir / "LectureDocGenerator.exe"
    if output_exe.exists():
        size_mb = output_exe.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print(" BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Executable Path : {output_exe}")
        print(f"Executable Size : {size_mb:.2f} MB")
        print("=" * 60)
        print("You can now distribute 'LectureDocGenerator.exe' to any Windows PC!")
    else:
        print("\n[Build Error] Executable was not found in dist directory.")

if __name__ == "__main__":
    build()
