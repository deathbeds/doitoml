# Ideas

## Robot tasks

- a `RobotSource` would synthesize a `raw_config` from a parser `.robot` file

```toml
*** Settings ***
# there's nowhere for arbitrary metadata at the suite level
Library     Operating System                        # reuse robot things
Library     dodo                                    # load a dodo.py as a module
Metadata    doitoml:prefix          robot           # configure doitoml
            doitoml:paths:input     input.html      # define variables
            doitoml:paths:output    output.html


*** Tasks ***       # also template tags
Copy the HTML
    [Tags]  file_dep::input  targets::output
    [Documentation]  this does a thing
    Copy File    ${input}  ${output}
```

## Preparse, expanding `Metadata` and `Tags`...

## Build up the variables for `robot.main`...

## When loaded into a CLI, this would look like...

    R ppt:html:build
    R robot:Copy the HTML

## Executed like...

```bash
doit "robot:Copy the HTML"
```

Would show...

```bash
. ppt:html:build
    ... updated html in python
. robot:Copy the HTML
    ROBOT TEST REPORT BEGINS
    ....
    PASSED
```
