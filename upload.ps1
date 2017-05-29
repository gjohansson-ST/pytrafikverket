py setup.py sdist bdist_wheel
pause
twine upload dist/*
Remove-Item ./dist/*