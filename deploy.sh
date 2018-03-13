C_GREEN="\033[0;32m"
C_RED="\033[0;31m"
NC="\033[0m"

VENV=/data/py3venv/bin/activate
. $VENV

HERE=$(dirname $0)
cd $HERE

[[ -f ".aws.sh" ]] && . ./.aws.sh

npm run build-assets --production \
    && npm run build-emails \
    && python3 manage.py collectstatic --noinput \
    && eb deploy

ret=$?

[[ $ret -ne 0 ]] \
    && { msg="failed";     color=$C_RED; } \
    || { msg="successful"; color=$C_GREEN; }

echo -e "${color}Deployment ${msg}.${NC}" >&2
exit $ret
