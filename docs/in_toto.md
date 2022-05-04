
# Vars
```bash
gpg_keyid=8ba69b87d43be294f23e812089a2ad3c07d962e8
git_org=lukpueh
git_repo=tuf

version=`python3 -c 'import tuf; print(tuf.__version__)'`
tag_name=v${version}

```

1. Git tag
```bash


in-toto-run \
  --step-name tag \
  --gpg ${gpg_keyid} \
  --materials . \
  --exclude '__pycache__' 'build' 'dist' 'htmlcov' '.?*' '*~' '*.egg-info' '*.pyc' \
  --metadata-directory .in_toto \
  -- git tag --sign ${tag_name} -m "${tag_name}"

```

2. Push to trigger CI/CD
```bash
git push ${git_org} ${tag_name}
````

3. Re-build sdist and generate attestation
```bash
in-toto-record start \
  --step-name sdist \
  --gpg ${gpg_keyid} \
  --materials . \
  --exclude '__pycache__' 'build' 'dist' 'htmlcov' '.?*' '*~' '*.egg-info' '*.pyc'

python3 -m build --sdist --outdir dist/ .

in-toto-record stop \
  --step-name sdist \
  --gpg ${gpg_keyid} \
  --products dist/tuf-${version}.tar.gz \
  --metadata-directory .in_toto
```

* Re-build wheel and generate attestation

```bash
in-toto-record start \
  --step-name wheel \
  --gpg ${gpg_keyid} \
  --materials . \
  --exclude '__pycache__' 'build' 'dist' 'htmlcov' '.?*' '*~' '*.egg-info' '*.pyc'

python3 -m build --wheel --outdir dist/ .

in-toto-record stop \
  --step-name wheel \
  --gpg ${gpg_keyid} \
  --products dist/tuf-${version}-py3-none-any.whl \
  --metadata-directory .in_toto
```

4. Download CD build attestations (".in_toto/{wheel, sdist}.{CI/CD KEY}.link)
```bash
rm .in_toto/*.5c98490d.link
wget -P .in_toto https://github.com/${git_org}/${git_repo}/releases/download/${tag_name}/wheel.5c98490d.link
wget -P .in_toto https://github.com/${git_org}/${git_repo}/releases/download/${tag_name}/sdist.5c98490d.link
```

5.1. Verify with root keys (currently only 8ba69b87d43be294f23e812089a2ad3c07d962e8)
```bash
in-toto-verify \
  --link-dir .in_toto \
  --layout .in_toto/sdist.layout \
  --gpg 8ba69b87d43be294f23e812089a2ad3c07d962e8

in-toto-verify \
  --link-dir .in_toto \
  --layout .in_toto/sdist.layout \
  --gpg 8ba69b87d43be294f23e812089a2ad3c07d962e8
```
