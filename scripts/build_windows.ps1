python -m nuitka `
  --standalone `
  --enable-plugin=pyside6 `
  --include-qt-plugins=qml `
  --windows-console-mode=disable `
  --output-dir=dist `
  --output-filename=NOVA.exe `
  --product-name=NOVA `
  --product-version=0.10.0 `
  --include-package=nova `
  --include-package-data=nova `
  --include-package=faster_whisper --include-package-data=faster_whisper `
  --include-package=piper --include-package-data=piper `
  --include-package=edge_tts `
  --include-package-data=_sounddevice_data `
  --include-data-dir=config=config `
  --include-data-dir=plugins=plugins `
  --nofollow-import-to=pytest `
  src/nova/launcher.py