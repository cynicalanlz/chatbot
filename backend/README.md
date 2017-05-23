```
pyenv virtualenv --system-site-packages 3.5.0 tapdone
pyenv local tapdone

pip install -r requirements/shared.txt
pip install -r requirements/dev.txt

py.test
```