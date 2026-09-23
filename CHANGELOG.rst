CHANGELOG
##########

Unreleased
++++++++++


v0.2.4
++++++++++

  - Expose extractor features from planner itself via `queue_extracted_registration()`.  Also simplifies `Loader`.

v0.2.3
++++++++++

  - Add cache warming feature for premaking mainly startup scoped services.
  - Add extended test examples.
  - Minor cleanups.

v0.2.2
++++++++++

  - Update README.rst and RELEASE.rst.
  - Add Injector to wrap callables for injecting dependencies.
  - Add callbacks for scanning for services.
  - Add hatch scripts for development.
  - Add dev deps to hatch default env.
  - Fix possible race condition(s) that would return different instances
    from container cache.

v0.2.1
+++++++

  - Initial version
