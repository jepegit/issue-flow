# Issue #248: option for not stopping in a cycle

Source: https://github.com/jepegit/issue-flow/issues/248

## Original issue text

Current behavior for iflow-cycle yolo is to stop if it experiences an issue that does not fulfill the yolo contract and it does not restart with the rest of the yolo issues (for example reporting "onfail:stop — remaining yolo issues were not started"). This should be a knob the user can set (config), e.g. allow_cycle_continuation.
