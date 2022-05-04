

1. Git tag
```bash
tag_name=v1.2.dev20
gpg_keyid=8ba69b87d43be294f23e812089a2ad3c07d962e8

in-toto-run \
  --step-name tag \
  --gpg ${gpg_keyid} \
  --metadata-directory .in_toto \
  --materials . \
  --exclude  '__pycache__' 'build' 'dist' 'htmlcov' '.?*' '*~' '*.egg-info' '*.pyc' \
  -- git tag --sign ${tag_name} -m "${tag_name}"

```

2. Push to trigger CI/CD
```bash
git push origin ${tag_name}
````

3. Re-build and generate attestations (.in_toto/{wheel, sdist}.{MY KEY}.link)
```bash
# FIXME: It is probably easier to just wrap `python3 -m build` in in-toto-run, here
# and in cd.yml, than maintaining a custom `hatch_build_in_toto.py` hook.
export HATCH_BUILD_HOOK_ENABLE_CUSTOM=true
export HATCH_IN_TOTO_GPG_KEYID=8ba69b87d43be294f23e812089a2ad3c07d962e8
python3 -m build --sdist --wheel --outdir dist/ .
```

4. Download CD build attestations (".in_toto/{wheel, sdist}.{CI/CD KEY}.link)
```bash
wget -P .in_toto https://github.com/{GITHUB_ORG}/{GITHUB_PROJECT}/releases/download/${tag_name}/sdist.5c98490d.link
wget -P .in_toto https://github.com/{GITHUB_ORG}/{GITHUB_PROJECT}/releases/download/${tag_name}/wheel.5c98490d.link
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
