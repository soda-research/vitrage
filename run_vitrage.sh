#!/usr/bin/env bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Vitrage Tempest tests"
  echo ""
  echo "  -h, --help               Print this usage message"
  echo "  -d, --debug              Run tests with testtools instead of testr. This allows you to use PDB"
  echo "  -t, --serial             Run testr serially"
  echo "  -c, --coverage           Generate coverage report"
  echo "  -- [TESTROPTIONS]        After the first '--' you can pass arbitrary arguments to testr "
}

testrargs=""
debug=0
serial=0
coverage=0
wrapper=""

if ! options=$(getopt -o VNnfuctphd -l help,debug,serial,coverage -- "$@")
then
    # parse error
    usage
    exit 1
fi

eval set -- $options
first_uu=yes
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit;;
    -d|--debug) debug=1;;
    -c|--coverage) coverage=1;;
    -t|--serial) serial=1;;
    --) [ "yes" == "$first_uu" ] || testrargs="$testrargs $1"; first_uu=no  ;;
    *) testrargs="$testrargs $1";;
  esac
  shift
done

cd `dirname "$0"`

function testr_init {
  if [ ! -d .testrepository ]; then
      ${wrapper} testr init
  fi
}

function run_tests {
  testr_init

  echo "run env"
  nosetests -vx vitrage_tempest_tests/tests/run_vitrage_env.py

  echo "run tests"
  ${wrapper} find . -type f -name "*.pyc" -delete
  export OS_TEST_PATH=./vitrage_tempest_tests/tests

  if [ "$testrargs" = "" ]; then
      testrargs="discover ../vitrage_tempest_tests/tests"
  fi

  if [ $debug -eq 1 ]; then
      ${wrapper} python -m testtools.run $testrargs
      return $?
  fi

  if [ $coverage -eq 1 ]; then
      ${wrapper} python setup.py test --coverage
      return $?
  fi

  if [ $serial -eq 1 ]; then
      ${wrapper} testr run --subunit $testrargs | ${wrapper} subunit-trace -n -f
  else
      ${wrapper} testr run --parallel --subunit $testrargs | ${wrapper} subunit-trace -n -f
  fi

  echo "stop env"
  nosetests -vx vitrage_tempest_tests/tests/stop_vitrage_env.py
}

run_tests
retval=$?

exit $retval