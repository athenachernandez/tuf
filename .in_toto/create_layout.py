from in_toto.models.layout import Inspection, Layout, Step
from in_toto.models.metadata import Metablock
from securesystemslib.gpg.functions import export_pubkeys

cd_key = {
    "keyid": "5c98490d78e6ac4401b065870b6f612587ff69dd89176099af95d1c4615afd8f",
    "keytype": "ed25519",
    "scheme": "ed25519",
    "keyval": {
        "public": "d685e2c2cfd1f2d79f5c301b25b3e0bc83f951c47d2d13a93d715fed721ca20d"
    },
}

maintainer_keyids = [
    "8ba69b87d43be294f23e812089a2ad3c07d962e8",
]

maintainer_keys = export_pubkeys(maintainer_keyids)


for build in ["sdist", "wheel"]:

    layout = Layout()
    layout.set_relative_expiration(months=12)

    for gpg_keyid in [cd_key] + list(maintainer_keys.values()):
        layout.add_functionary_key(gpg_keyid)

    tag_step = Step(name="tag")
    tag_step.pubkeys = maintainer_keyids
    tag_step.threshold = 1

    build_step = Step(name=build)
    build_step.pubkeys = [cd_key["keyid"]] + maintainer_keyids
    build_step.threshold = 2
    build_step.add_material_rule_from_string("MATCH * WITH MATERIALS FROM tag")
    build_step.add_material_rule_from_string("DISALLOW *")

    layout.steps = [tag_step, build_step]

    metablock = Metablock(signed=layout)
    metablock.dump(f"{build}.layout")

    # Sign layouts in CLI
    # in-toto-sign -g 8ba69b87d43be294f23e812089a2ad3c07d962e8 -f sdist.layout
    # in-toto-sign -g 8ba69b87d43be294f23e812089a2ad3c07d962e8 -f wheel.layout
