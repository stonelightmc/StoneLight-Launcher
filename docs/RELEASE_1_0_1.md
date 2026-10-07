# StoneLight Launcher 1.0.1

## Hotfix

This release fixes custom instance cloning.

## Fixed

- Cloning could create the new instance folder but fail to show the cloned
  instance in the launcher list.
- Clone IDs now check both `instances.json` and already existing folders in
  `data/instances`.
- Cloning now copies into a temporary `.__cloning__` folder first and moves it to
  the final folder only after the copy succeeds.
- Failed clone attempts clean up temporary/final clone folders more reliably.
- The Web UI now explicitly refreshes `get_app_state` after cloning and selects
  the cloned instance.

## Notes

- Existing orphan folders from previous failed clone attempts are not deleted
  automatically.
- If such folders are no longer needed, they can be removed manually from
  `data/instances`.
