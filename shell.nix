let
  pkgs = import <nixpkgs> {};
  python = pkgs.python3;
  pythonPackages = python.pkgs;
in

pkgs.mkShell {
  name = "nanoDAQ";
  buildInputs = with pythonPackages; [
    # Auto completion
    jedi

    # Linters
    flake8
    pylint

    # Python requirements (enough to get a virtualenv going).
    virtualenvwrapper
  ];

  shellHook = ''
    # Allow the use of wheels.
    SOURCE_DATE_EPOCH=$(date +%s)

    # Augment the dynamic linker path or other packages you care about
    #export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.ncurses}/lib

    if test -d $HOME/build/python-venv; then
      VENV=$HOME/build/python-venv/nanoDAQ
    else
      VENV=./.virtualenv
    fi

    if test ! -d $VENV; then
      virtualenv $VENV
    fi
    source $VENV/bin/activate

    # allow for the environment to pick up packages installed with virtualenv
    export PYTHONPATH=$VENV/${python.sitePackages}/:$PYTHONPATH
  '';
}
