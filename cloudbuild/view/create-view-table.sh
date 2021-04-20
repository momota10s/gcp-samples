# /bin/bash

set -eu -o pipefail
for pathfile in sql/*.sql ; do
  echo $pathfile
  bq query --use_legacy_sql=false < $pathfile
done

