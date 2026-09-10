#!/usr/bin/env bash
set -euo pipefail
cp android-youtube-test/madre001/build_candidate003_keybox.sh /tmp/build_candidate003_keybox.sh
sed -i "/geovision_google_maps_api_key_1/d;/geovision_google_maps_api_key_2/d;/geovision_google_maps_api_key_3/d" /tmp/build_candidate003_keybox.sh
bash /tmp/build_candidate003_keybox.sh
