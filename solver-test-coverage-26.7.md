I'm posting a coverage analysis here against conda 26.7.0:

## Some notes on the environment and generation

- conda was installed at tag `26.7.0`, conda-libmamba-solver at 26.7.0, with the Python 3.10 devenv and miniforge
- `--benchmark-disable` is required, because tests using the `benchmark` fixture run the solver inside the benchmark harness, which coverage cannot trace, so without the flag they go missing from this list entirely
- The covan specs: `conda/core/solve.py:325-511` (classic `Solver.solve_final_state`) and `**/conda_libmamba_solver/solver.py:138-192` (`LibMambaSolver.solve_final_state`). These line ranges are version-specific and thus were recomputed by `ast` for 26.7.0.

## Summary

- Tests touching the classic solver: 219 across 13 files
- Tests touching the libmamba solver: 299 across 35 files
- Union: 352 tests across 39 files
- Since 26.3: 72 tests are new, 73 are gone or renamed.
- 108 of the 352 have at least one ported YAML item on `main` or an open PR branch

## Solver lines reached only by unported tests

With line-level context data, we can ask the question the checkbox list below cannot answer, i.e., about which solver code paths the ported suite misses entirely.

- libmamba solver: none, as every line of `LibMambaSolver.solve_final_state` reached by any test is also reached by at least one ported test.
- classic solver: 6 lines, all in diagnostics or guard paths:
  - `conda/core/solve.py:372-373`: the no-channels error guard. It's only reached by `test_no_channels_error` (new since 26.3).
  - `conda/core/solve.py:448-449`: the "unsuccessful initial attempt using frozen solve, retrying with flexible solve" message. This is reached only by CLI-level installs into existing environments (`test_create.py`, CLI tests, and `test_features.py`).
  - `conda/core/solve.py:453-454`: the "retrying with next repodata source" fallback message. This is in `test_current_repodata_usage` territory, which is a solver-file test that cannot be ported without `repodata_fn` support in the harness

Everything else is exercised by the ported YAML suite.

## New tests since conda version 26.3

<details>
<summary>72 tests not in the list above</summary>

- `tests/cli/test_cli_install.py::test_find_conflicts_called_once`
- `tests/cli/test_cli_install.py::test_frozen_env_cep22`
- `tests/cli/test_env.py::test_conda_create_with_pip_json_output`
- `tests/cli/test_main_compare.py::test_get_packages`
- `tests/cli/test_main_env_create.py::test_env_create_with_invalid_installer`
- `tests/cli/test_main_export.py::test_export_explicit_format_validation_errors`
- `tests/cli/test_main_export.py::test_export_multiple_platforms`
- `tests/cli/test_main_export.py::test_export_non_pip_env_warnings`
- `tests/cli/test_main_export.py::test_export_single_platform_different_platform`
- `tests/cli/test_main_export.py::test_export_warnings`
- `tests/cli/test_main_export.py::test_export_with_pip_dependencies_integration`
- `tests/cli/test_main_info.py::test_compute_prefix_size`
- `tests/cli/test_main_install.py::test_build_version_shows_as_changed`
- `tests/cli/test_main_install.py::test_install_revision_revert`
- `tests/cli/test_main_list.py::test_fields_dependent`
- `tests/cli/test_main_list.py::test_list_size`
- `tests/cli/test_main_list.py::test_list_size_empty_paths_data`
- `tests/cli/test_main_list.py::test_list_size_json`
- `tests/cli/test_main_notices.py::test_notices_shown_after_previous_command_error`
- `tests/cli/test_main_run.py::test_no_newline_in_output`
- `tests/cli/test_main_run.py::test_run_with_separator`
- `tests/cli/test_main_update.py::test_update`
- `tests/core/test_prefix_data.py::test_api_consistency`
- `tests/core/test_prefix_data.py::test_get_conda_packages_returns_sorted_list`
- `tests/core/test_prefix_data.py::test_get_packages_behavior_with_interoperability`
- `tests/core/test_prefix_data.py::test_get_python_packages_basic_functionality`
- `tests/core/test_prefix_data.py::test_get_python_packages_with_pip_interoperability`
- `tests/core/test_prefix_data.py::test_method_consistency`
- `tests/core/test_prefix_data.py::test_package_extraction_methods_types`
- `tests/core/test_prefix_data.py::test_package_extraction_package_counts`
- `tests/core/test_prefix_data.py::test_prefix_insertion_error`
- `tests/core/test_prefix_data.py::test_timestamps`
- `tests/core/test_solve.py::test_broken_install`
- `tests/core/test_solve.py::test_globstr_matchspec_compatible`
- `tests/core/test_solve.py::test_globstr_matchspec_non_compatible`
- `tests/core/test_solve.py::test_no_channels_error`
- `tests/core/test_solve.py::test_solve_2`
- `tests/core/test_solve.py::test_strict_custom_multichannel_allows_fallback_to_later_subchannel`
- `tests/core/test_solve.py::test_virtual_package_solver`
- `tests/env/test_create.py::test_create_env_custom_platform`
- `tests/env/test_create.py::test_create_env_from_environment_yml_does_not_output_duplicate_warning`
- `tests/env/test_create.py::test_create_env_from_file_with_mismatched_extension_via_env_spec`
- `tests/env/test_create.py::test_export_and_recreate_environment`
- `tests/env/test_env.py::test_create_and_update_env_with_just_vars`
- `tests/env/test_env.py::test_env_advanced_pip`
- `tests/models/test_environment.py::test_extrapolate`
- `tests/models/test_environment.py::test_extrapolate_virtualdep_package`
- `tests/models/test_environment.py::test_from_prefix_behavior_with_pip_interoperability`
- `tests/models/test_environment.py::test_from_prefix_options_affect_correct_packages`
- `tests/models/test_environment.py::test_from_prefix_package_population_semantics`
- `tests/models/test_records.py::test_requested_spec`
- `tests/plugins/subcommands/doctor/health_checks/test_consistency.py::test_env_consistency_check_passes`
- `tests/plugins/test_environment_export.py::test_compare_export_commands`
- `tests/plugins/test_transaction_hooks.py::test_post_transaction_raises_exception`
- `tests/plugins/test_transaction_hooks.py::test_pre_transaction_raises_exception`
- `tests/plugins/test_transaction_hooks.py::test_transaction_hooks_invoked`
- `tests/shell/test_shell.py::test_activate_deactivate_modify_path`
- `tests/shell/test_shell.py::test_stacking`
- `tests/test_activate.py::test_activate_default_env`
- `tests/test_create.py::test_clone_env_missing_channel_metadata`
- `tests/test_create.py::test_clone_env_with_conda`
- `tests/test_create.py::test_create_cleanup_on_clobber_error`
- `tests/test_create.py::test_create_download_only_without_prefix`
- `tests/test_create.py::test_create_multiple_files_with_cli_prefix`
- `tests/test_create.py::test_create_name_overrides_file`
- `tests/test_create.py::test_create_with_env_variables_are_set_correctly`
- `tests/test_create.py::test_dont_remove_conda`
- `tests/test_create.py::test_dont_remove_conda_dependency_with_dependent_packages`
- `tests/test_create.py::test_install_multiple_files_with_cli_prefix`
- `tests/test_create.py::test_install_preserves_prefix_on_clobber_error`
- `tests/test_create.py::test_install_succeeds_with_clobber_flag`
- `tests/test_create.py::test_transactional_rollback_create_keeps_preexisting_directory`
</details>

## Gone since conda version 26.3

<details>
<summary>73 tests from the list above no longer present at 26.7 (removed, renamed, or no longer touching the solver)</summary>

- `tests/cli/test_common.py::test_print_envs_list`
- `tests/cli/test_common.py::test_print_envs_list_output_false`
- `tests/cli/test_config.py::test_conda_config_describe`
- `tests/cli/test_config.py::test_conda_config_validate`
- `tests/cli/test_config.py::test_conda_config_validate_sslverify_truststore`
- `tests/cli/test_main_install.py::test_install_mkdir`
- `tests/cli/test_main_rename.py::test_rename_with_force_with_errors_prefix`
- `tests/cli/test_main_run.py::test_run_readonly_env`
- `tests/cli/test_main_run.py::test_run_returns_int`
- `tests/cli/test_main_run.py::test_run_returns_nonzero_errorlevel`
- `tests/cli/test_main_run.py::test_run_returns_zero_errorlevel`
- `tests/cli/test_main_run.py::test_run_uncaptured`
- `tests/cli/test_subcommands.py::test_compare`
- `tests/cli/test_subcommands.py::test_env_config_vars`
- `tests/cli/test_subcommands.py::test_env_remove`
- `tests/cli/test_subcommands.py::test_package`
- `tests/cli/test_subcommands.py::test_remove`
- `tests/cli/test_subcommands.py::test_rename`
- `tests/core/test_index.py::test__supplement_index_with_prefix`
- `tests/core/test_index.py::test__supplement_index_with_prefix_index_class`
- `tests/core/test_prefix_data.py::test_get_environment_env_vars`
- `tests/core/test_prefix_data.py::test_set_unset_environment_env_vars`
- `tests/core/test_prefix_data.py::test_set_unset_environment_env_vars_no_exist`
- `tests/core/test_solve.py::test_cuda_glibc_sat`
- `tests/core/test_solve.py::test_determine_constricting_specs_conflicts`
- `tests/core/test_solve.py::test_determine_constricting_specs_conflicts_upperbound`
- `tests/core/test_solve.py::test_determine_constricting_specs_multi_conflicts`
- `tests/core/test_solve.py::test_determine_constricting_specs_no_conflicts_free`
- `tests/core/test_solve.py::test_determine_constricting_specs_no_conflicts_no_upperbound`
- `tests/core/test_solve.py::test_determine_constricting_specs_no_conflicts_upperbound_compound_depends`
- `tests/core/test_solve.py::test_determine_constricting_specs_no_conflicts_version_star`
- `tests/env/test_create.py::test_protected_dirs_error_for_env_create`
- `tests/env/test_env.py::test_create_advanced_pip`
- `tests/gateways/test_connection.py::test_s3_server`
- `tests/gateways/test_connection.py::test_s3_server_with_mock`
- `tests/gateways/test_logging.py::test_token_not_present_in_conda_create`
- `tests/plugins/subcommands/doctor/test_cli.py::test_conda_doctor_with_test_environment`
- `tests/test_activate.py::test_activate_same_environment`
- `tests/test_activate.py::test_build_activate_dont_activate_unset_var`
- `tests/test_activate.py::test_build_activate_restore_unset_env_vars`
- `tests/test_activate.py::test_build_activate_shlvl_0`
- `tests/test_activate.py::test_build_activate_shlvl_1`
- `tests/test_activate.py::test_build_activate_shlvl_warn_clobber_vars`
- `tests/test_activate.py::test_build_deactivate_shlvl_1`
- `tests/test_activate.py::test_build_deactivate_shlvl_2_from_activate`
- `tests/test_activate.py::test_build_deactivate_shlvl_2_from_stack`
- `tests/test_activate.py::test_build_stack_shlvl_1`
- `tests/test_activate.py::test_get_env_vars_big_whitespace`
- `tests/test_activate.py::test_get_env_vars_empty_file`
- `tests/test_create.py::test_conda_downgrade`
- `tests/test_create.py::test_conda_update_package_not_installed`
- `tests/test_create.py::test_create_dry_run_yes_safety`
- `tests/test_create.py::test_dont_remove_conda_1`
- `tests/test_create.py::test_dont_remove_conda_2`
- `tests/test_create.py::test_install_bound_virtual_package`
- `tests/test_create.py::test_neutering_of_historic_specs`
- `tests/test_create.py::test_not_writable_env_raises_EnvironmentNotWritableError`
- `tests/test_create.py::test_run_script_called`
- `tests/test_create.py::test_strict_resolve_get_reduced_index`
- `tests/test_plan.py::test_pinned_specs_all`
- `tests/test_plan.py::test_pinned_specs_conda_meta_pinned`
- `tests/test_plan.py::test_pinned_specs_condarc`
- `tests/test_shell.py::test_activate_deactivate_modify_path`
- `tests/test_shell.py::test_bash_activate_error`
- `tests/test_shell.py::test_basic_integration`
- `tests/test_shell.py::test_legacy_activate_deactivate_bash`
- `tests/test_shell.py::test_powershell_basic_integration`
- `tests/test_shell.py::test_stacking`
- `tests/test_solvers.py::TestClassicSolver.test_channel_priority_1`
- `tests/test_solvers.py::TestLibMambaSolver.test_channel_priority_1`
- `tests/testing/test_fixtures.py::test_env`
- `tests/testing/test_fixtures.py::test_session_tmp_env`
- `tests/testing/test_fixtures.py::test_tmp_env`
</details>

## Full list per conda version 26.7

`[x]` means that at least one ported YAML item references this test, via provenance `node_id`s. It does not mean that every stage or assertion of the original is covered, and that is separately measured.

<details>
<summary><code>tests/cli/test_cli_install.py</code> (0/4 ported)</summary>

- [ ] `test_emscripten_forge`
- [ ] `test_find_conflicts_called_once`
- [ ] `test_frozen_env_cep22`
- [ ] `test_pre_link_message`
</details>
<details>
<summary><code>tests/cli/test_compare.py</code> (0/2 ported)</summary>

- [ ] `test_compare_fail`
- [ ] `test_compare_success`
</details>
<details>
<summary><code>tests/cli/test_env.py</code> (0/22 ported)</summary>

- [ ] `test_conda_create_with_pip_json_output`
- [ ] `test_conda_env_create_http`
- [ ] `test_create_dry_run_json`
- [ ] `test_create_dry_run_yaml`
- [ ] `test_create_unsolvable_env`
- [ ] `test_create_valid_env`
- [ ] `test_create_valid_env_json_output`
- [ ] `test_create_valid_env_with_conda_and_pip_json_output`
- [ ] `test_create_valid_env_with_variables`
- [ ] `test_env_export`
- [ ] `test_env_export_json`
- [ ] `test_env_export_with_variables`
- [ ] `test_export_multi_channel`
- [ ] `test_list`
- [ ] `test_name_override`
- [ ] `test_pip_error_is_propagated`
- [ ] `test_remove_dry_run`
- [ ] `test_set_unset_env_vars`
- [ ] `test_update`
- [ ] `test_update_env_json_output`
- [ ] `test_update_env_no_action_json_output`
- [ ] `test_update_env_only_pip_json_output`
</details>
<details>
<summary><code>tests/cli/test_main_clean.py</code> (0/8 ported)</summary>

- [ ] `test_clean_all`
- [ ] `test_clean_all_mock_lstat`
- [ ] `test_clean_and_packages`
- [ ] `test_clean_force_pkgs_dirs`
- [ ] `test_clean_index_cache`
- [ ] `test_clean_logfiles`
- [ ] `test_clean_tarballs`
- [ ] `test_clean_tempfiles`
</details>
<details>
<summary><code>tests/cli/test_main_compare.py</code> (0/1 ported)</summary>

- [ ] `test_get_packages`
</details>
<details>
<summary><code>tests/cli/test_main_env_create.py</code> (0/1 ported)</summary>

- [ ] `test_env_create_with_invalid_installer`
</details>
<details>
<summary><code>tests/cli/test_main_export.py</code> (0/6 ported)</summary>

- [ ] `test_export_explicit_format_validation_errors`
- [ ] `test_export_multiple_platforms`
- [ ] `test_export_non_pip_env_warnings`
- [ ] `test_export_single_platform_different_platform`
- [ ] `test_export_warnings`
- [ ] `test_export_with_pip_dependencies_integration`
</details>
<details>
<summary><code>tests/cli/test_main_info.py</code> (0/1 ported)</summary>

- [ ] `test_compute_prefix_size`
</details>
<details>
<summary><code>tests/cli/test_main_install.py</code> (1/5 ported)</summary>

- [ ] `test_build_version_shows_as_changed`
- [ ] `test_conda_pip_interop_dependency_satisfied_by_pip`
- [x] `test_install_freezes_env_by_default`
- [ ] `test_install_from_extracted_package`
- [ ] `test_install_revision_revert`
</details>
<details>
<summary><code>tests/cli/test_main_list.py</code> (0/10 ported)</summary>

- [ ] `test_explicit`
- [ ] `test_export`
- [ ] `test_fields_dependent`
- [ ] `test_list`
- [ ] `test_list_explicit`
- [ ] `test_list_reverse`
- [ ] `test_list_size`
- [ ] `test_list_size_empty_paths_data`
- [ ] `test_list_size_json`
- [ ] `test_list_specific_version`
</details>
<details>
<summary><code>tests/cli/test_main_notices.py</code> (0/3 ported)</summary>

- [ ] `test_notices_appear_once_when_running_decorated_commands`
- [ ] `test_notices_does_not_interrupt_command_on_failure`
- [ ] `test_notices_shown_after_previous_command_error`
</details>
<details>
<summary><code>tests/cli/test_main_remove.py</code> (0/3 ported)</summary>

- [ ] `test_remove_all`
- [ ] `test_remove_all_keep_env`
- [ ] `test_remove_globbed_package_names`
</details>
<details>
<summary><code>tests/cli/test_main_rename.py</code> (0/10 ported)</summary>

- [ ] `test_cannot_rename_active_env_by_name`
- [ ] `test_protected_dirs_error_for_rename`
- [ ] `test_rename_by_name_name_already_exists_error`
- [ ] `test_rename_by_name_success`
- [ ] `test_rename_by_path_path_already_exists_error`
- [ ] `test_rename_by_path_success`
- [ ] `test_rename_with_dry_run`
- [ ] `test_rename_with_force`
- [ ] `test_rename_with_force_and_dry_run`
- [ ] `test_rename_with_force_with_errors`
</details>
<details>
<summary><code>tests/cli/test_main_run.py</code> (0/3 ported)</summary>

- [ ] `test_multiline_run_command`
- [ ] `test_no_newline_in_output`
- [ ] `test_run_with_separator`
</details>
<details>
<summary><code>tests/cli/test_main_update.py</code> (0/1 ported)</summary>

- [ ] `test_update`
</details>
<details>
<summary><code>tests/cli/test_subcommands.py</code> (0/8 ported)</summary>

- [ ] `test_create`
- [ ] `test_env_create`
- [ ] `test_env_update`
- [ ] `test_install`
- [ ] `test_list`
- [ ] `test_remove_all_json`
- [ ] `test_run`
- [ ] `test_update`
</details>
<details>
<summary><code>tests/core/test_index.py</code> (0/13 ported)</summary>

- [ ] `TestIndex.test_cache_entries`
- [ ] `TestIndex.test_contains_invalid`
- [ ] `TestIndex.test_contains_valid`
- [ ] `TestIndex.test_copy`
- [ ] `TestIndex.test_getitem_cache`
- [ ] `TestIndex.test_getitem_channel`
- [ ] `TestIndex.test_getitem_channel_invalid`
- [ ] `TestIndex.test_getitem_feature`
- [ ] `TestIndex.test_getitem_feature_non_existent`
- [ ] `TestIndex.test_getitem_prefix`
- [ ] `TestIndex.test_getitem_system_package_invalid`
- [ ] `TestIndex.test_getitem_system_package_valid`
- [ ] `TestIndex.test_reduced_index`
</details>
<details>
<summary><code>tests/core/test_prefix_data.py</code> (0/10 ported)</summary>

- [ ] `test_api_consistency`
- [ ] `test_get_conda_packages_returns_sorted_list`
- [ ] `test_get_packages_behavior_with_interoperability`
- [ ] `test_get_python_packages_basic_functionality`
- [ ] `test_get_python_packages_with_pip_interoperability`
- [ ] `test_method_consistency`
- [ ] `test_package_extraction_methods_types`
- [ ] `test_package_extraction_package_counts`
- [ ] `test_prefix_insertion_error`
- [ ] `test_timestamps`
</details>
<details>
<summary><code>tests/core/test_solve.py</code> (42/49 ported)</summary>

- [x] `test_aggressive_update_packages`
- [ ] `test_archspec_call`
- [x] `test_auto_update_conda`
- [ ] `test_broken_install`
- [x] `test_channel_priority_churn_minimized`
- [x] `test_conda_downgrade`
- [x] `test_cuda_1`
- [x] `test_cuda_2`
- [x] `test_cuda_constrain_absent`
- [x] `test_cuda_fail_1`
- [x] `test_cuda_fail_2`
- [ ] `test_current_repodata_fallback`
- [ ] `test_current_repodata_usage`
- [x] `test_downgrade_python_prevented_with_sane_message`
- [x] `test_explicit_conda_downgrade`
- [x] `test_fast_update_with_update_modifier_not_set`
- [x] `test_features_solve_1`
- [x] `test_force_reinstall_1`
- [x] `test_force_reinstall_2`
- [x] `test_force_remove_1`
- [x] `test_freeze_deps_1`
- [x] `test_globstr_matchspec_compatible`
- [x] `test_globstr_matchspec_non_compatible`
- [x] `test_indirect_dep_optimized_by_version_over_package_count`
- [ ] `test_no_channels_error`
- [x] `test_no_deps_1`
- [x] `test_no_update_deps_1`
- [x] `test_only_deps_1`
- [x] `test_only_deps_2`
- [x] `test_pinned_1`
- [x] `test_priority_1`
- [x] `test_prune_1`
- [x] `test_python2_update`
- [x] `test_remove_with_constrained_dependencies`
- [x] `test_solve_1`
- [x] `test_solve_2`
- [x] `test_solve_msgs_exclude_vp`
- [ ] `test_strict_custom_multichannel_allows_fallback_to_later_subchannel`
- [x] `test_timestamps_1`
- [x] `test_unfreeze_when_required`
- [x] `test_update_all_1`
- [x] `test_update_deps_1`
- [x] `test_update_deps_2`
- [x] `test_update_prune_1`
- [x] `test_update_prune_2`
- [x] `test_update_prune_3`
- [x] `test_update_prune_4`
- [x] `test_update_prune_5`
- [ ] `test_virtual_package_solver`
</details>
<details>
<summary><code>tests/env/test_create.py</code> (0/11 ported)</summary>

- [ ] `test_create_advanced_pip`
- [ ] `test_create_empty_env`
- [ ] `test_create_env_custom_platform`
- [ ] `test_create_env_default_packages`
- [ ] `test_create_env_from_environment_yml_does_not_output_duplicate_warning`
- [ ] `test_create_env_from_file_with_mismatched_extension_via_env_spec`
- [ ] `test_create_env_json`
- [ ] `test_create_env_no_default_packages`
- [ ] `test_create_update`
- [ ] `test_create_update_remote_env_file`
- [ ] `test_export_and_recreate_environment`
</details>
<details>
<summary><code>tests/env/test_env.py</code> (0/2 ported)</summary>

- [ ] `test_create_and_update_env_with_just_vars`
- [ ] `test_env_advanced_pip`
</details>
<details>
<summary><code>tests/models/test_environment.py</code> (0/5 ported)</summary>

- [ ] `test_extrapolate`
- [ ] `test_extrapolate_virtualdep_package`
- [ ] `test_from_prefix_behavior_with_pip_interoperability`
- [ ] `test_from_prefix_options_affect_correct_packages`
- [ ] `test_from_prefix_package_population_semantics`
</details>
<details>
<summary><code>tests/models/test_prefix_graph.py</code> (0/7 ported)</summary>

- [ ] `test_deep_cyclical_dependency`
- [ ] `test_prefix_graph_1`
- [ ] `test_prefix_graph_2`
- [ ] `test_remove_youngest_descendant_nodes_with_specs`
- [ ] `test_sort_without_prep`
- [ ] `test_windows_sort_orders_1`
- [ ] `test_windows_sort_orders_2`
</details>
<details>
<summary><code>tests/models/test_records.py</code> (0/1 ported)</summary>

- [ ] `test_requested_spec`
</details>
<details>
<summary><code>tests/plugins/subcommands/doctor/health_checks/test_consistency.py</code> (0/1 ported)</summary>

- [ ] `test_env_consistency_check_passes`
</details>
<details>
<summary><code>tests/plugins/test_environment_export.py</code> (0/1 ported)</summary>

- [ ] `test_compare_export_commands`
</details>
<details>
<summary><code>tests/plugins/test_post_solves.py</code> (0/2 ported)</summary>

- [ ] `test_post_solve_action_raises_exception`
- [ ] `test_post_solve_invoked`
</details>
<details>
<summary><code>tests/plugins/test_pre_solves.py</code> (0/1 ported)</summary>

- [ ] `test_pre_solve_invoked`
</details>
<details>
<summary><code>tests/plugins/test_transaction_hooks.py</code> (0/3 ported)</summary>

- [ ] `test_post_transaction_raises_exception`
- [ ] `test_pre_transaction_raises_exception`
- [ ] `test_transaction_hooks_invoked`
</details>
<details>
<summary><code>tests/shell/test_shell.py</code> (0/2 ported)</summary>

- [ ] `test_activate_deactivate_modify_path`
- [ ] `test_stacking`
</details>
<details>
<summary><code>tests/test_activate.py</code> (0/1 ported)</summary>

- [ ] `test_activate_default_env`
</details>
<details>
<summary><code>tests/test_api.py</code> (0/1 ported)</summary>

- [ ] `test_Solver_return_value_contract`
</details>
<details>
<summary><code>tests/test_create.py</code> (0/80 ported)</summary>

- [ ] `test_allow_softlinks`
- [ ] `test_channel_usage_replacing_python`
- [ ] `test_clone_env_missing_channel_metadata`
- [ ] `test_clone_env_with_conda`
- [ ] `test_clone_offline_simple`
- [ ] `test_clone_offline_with_untracked`
- [ ] `test_compile_pyc`
- [ ] `test_conda_pip_interop_conda_editable_package`
- [ ] `test_create_cleanup_on_clobber_error`
- [ ] `test_create_default_packages`
- [ ] `test_create_default_packages_no_default_packages`
- [ ] `test_create_download_only_without_prefix`
- [ ] `test_create_dry_run`
- [ ] `test_create_dry_run_json`
- [ ] `test_create_dry_run_without_prefix`
- [ ] `test_create_empty_env`
- [ ] `test_create_env_different_platform`
- [ ] `test_create_install_update_remove_smoketest`
- [ ] `test_create_multiple_files_with_cli_prefix`
- [ ] `test_create_name_overrides_file`
- [ ] `test_create_no_deps_flag`
- [ ] `test_create_only_deps_flag`
- [ ] `test_create_override_channels_enabled`
- [ ] `test_create_with_env_variables_are_set_correctly`
- [ ] `test_cross_channel_incompatibility`
- [ ] `test_disallowed_packages`
- [ ] `test_dont_remove_conda`
- [ ] `test_dont_remove_conda_dependency_with_dependent_packages`
- [ ] `test_download_only_flag`
- [ ] `test_force_remove`
- [ ] `test_install_broken_post_install_keeps_existing_folders`
- [ ] `test_install_force_reinstall_flag`
- [ ] `test_install_multiple_files_with_cli_prefix`
- [ ] `test_install_only_deps_flag`
- [ ] `test_install_preserves_prefix_on_clobber_error`
- [ ] `test_install_prune_flag`
- [ ] `test_install_python_and_search`
- [ ] `test_install_succeeds_with_clobber_flag`
- [ ] `test_install_tarball_from_file_based_channel`
- [ ] `test_install_update_deps_flag`
- [ ] `test_install_update_deps_only_deps_flags`
- [ ] `test_install_virtual_packages`
- [ ] `test_json_create_install_update_remove`
- [ ] `test_list_with_pip_no_binary`
- [ ] `test_list_with_pip_wheel`
- [ ] `test_menuinst_v2`
- [ ] `test_noarch_generic_package`
- [ ] `test_noarch_python_package_reinstall_on_pyver_change`
- [ ] `test_noarch_python_package_with_entry_points`
- [ ] `test_noarch_python_package_without_entry_points`
- [ ] `test_nonadmin_file_untouched`
- [ ] `test_offline_with_empty_index_cache`
- [ ] `test_package_cache_regression`
- [ ] `test_package_optional_pinning`
- [ ] `test_package_pinning`
- [ ] `test_packages_not_found`
- [ ] `test_pinned_override_with_explicit_spec`
- [ ] `test_post_link_run_in_env`
- [ ] `test_python_site_packages_path`
- [ ] `test_remove_empty_env`
- [ ] `test_remove_force_remove_flag`
- [ ] `test_remove_spellcheck`
- [ ] `test_repodata_v2_base_url`
- [ ] `test_rm_rf`
- [ ] `test_run_preserves_arguments`
- [ ] `test_safety_checks_disabled`
- [ ] `test_safety_checks_enabled`
- [ ] `test_safety_checks_warn`
- [ ] `test_shortcut_absent_does_not_barf_on_uninstall`
- [ ] `test_shortcut_absent_when_condarc_set`
- [ ] `test_shortcut_creation_installs_shortcut`
- [ ] `test_tarball_install`
- [ ] `test_tarball_install_and_bad_metadata`
- [ ] `test_transactional_rollback_create_keeps_preexisting_directory`
- [ ] `test_transactional_rollback_simple`
- [ ] `test_transactional_rollback_upgrade_downgrade`
- [ ] `test_update_all_updates_pip_pkg`
- [ ] `test_update_deps_flag_absent`
- [ ] `test_update_deps_flag_present`
- [ ] `test_update_with_pinned_packages`
</details>
<details>
<summary><code>tests/test_features.py</code> (0/4 ported)</summary>

- [ ] `test_install_track_features_downgrade`
- [ ] `test_install_track_features_upgrade`
- [ ] `test_remove_features_downgrade`
- [ ] `test_remove_features_upgrade`
</details>
<details>
<summary><code>tests/test_link_order.py</code> (0/2 ported)</summary>

- [ ] `test_link_order_post_link_actions`
- [ ] `test_link_order_post_link_depend`
</details>
<details>
<summary><code>tests/test_misc.py</code> (0/1 ported)</summary>

- [ ] `test_explicit_missing_cache_entries`
</details>
<details>
<summary><code>tests/test_priority.py</code> (0/1 ported)</summary>

- [ ] `test_reorder_channel_priority`
</details>
<details>
<summary><code>tests/test_solvers.py</code> (65/65 ported)</summary>

- [x] `TestClassicSolver.test_accelerate`
- [x] `TestClassicSolver.test_anaconda_nomkl`
- [x] `TestClassicSolver.test_arch_preferred_over_noarch_when_otherwise_equal`
- [x] `TestClassicSolver.test_circular_dependencies`
- [x] `TestClassicSolver.test_empty`
- [x] `TestClassicSolver.test_get_dists`
- [x] `TestClassicSolver.test_get_reduced_index_broadening_preferred_solution`
- [x] `TestClassicSolver.test_get_reduced_index_broadening_with_unsatisfiable_early_dep`
- [x] `TestClassicSolver.test_install_package_with_feature`
- [x] `TestClassicSolver.test_iopro_mkl`
- [x] `TestClassicSolver.test_iopro_nomkl`
- [x] `TestClassicSolver.test_irrational_version`
- [x] `TestClassicSolver.test_mkl`
- [x] `TestClassicSolver.test_no_features`
- [x] `TestClassicSolver.test_noarch_preferred_over_arch_when_build_greater`
- [x] `TestClassicSolver.test_noarch_preferred_over_arch_when_build_greater_dep`
- [x] `TestClassicSolver.test_noarch_preferred_over_arch_when_version_greater`
- [x] `TestClassicSolver.test_noarch_preferred_over_arch_when_version_greater_dep`
- [x] `TestClassicSolver.test_nonexistent`
- [x] `TestClassicSolver.test_nonexistent_deps`
- [x] `TestClassicSolver.test_pseudo_boolean`
- [x] `TestClassicSolver.test_remove`
- [x] `TestClassicSolver.test_scipy_mkl`
- [x] `TestClassicSolver.test_surplus_features_1`
- [x] `TestClassicSolver.test_surplus_features_2`
- [x] `TestClassicSolver.test_timestamps_and_deps`
- [x] `TestClassicSolver.test_unintentional_feature_downgrade`
- [x] `TestClassicSolver.test_unsat_any_two_not_three`
- [x] `TestClassicSolver.test_unsat_chain`
- [x] `TestClassicSolver.test_unsat_channel_priority`
- [x] `TestClassicSolver.test_unsat_expand_single`
- [x] `TestClassicSolver.test_unsat_from_r1`
- [x] `TestClassicSolver.test_unsat_missing_dep`
- [x] `TestClassicSolver.test_unsat_shortest_chain_1`
- [x] `TestClassicSolver.test_unsat_shortest_chain_2`
- [x] `TestClassicSolver.test_unsat_shortest_chain_3`
- [x] `TestClassicSolver.test_unsat_shortest_chain_4`
- [x] `TestClassicSolver.test_unsat_simple`
- [x] `TestLibMambaSolver.test_anaconda_nomkl`
- [x] `TestLibMambaSolver.test_arch_preferred_over_noarch_when_otherwise_equal`
- [x] `TestLibMambaSolver.test_circular_dependencies`
- [x] `TestLibMambaSolver.test_empty`
- [x] `TestLibMambaSolver.test_get_dists`
- [x] `TestLibMambaSolver.test_get_reduced_index_broadening_preferred_solution`
- [x] `TestLibMambaSolver.test_get_reduced_index_broadening_with_unsatisfiable_early_dep`
- [x] `TestLibMambaSolver.test_install_package_with_feature`
- [x] `TestLibMambaSolver.test_irrational_version`
- [x] `TestLibMambaSolver.test_noarch_preferred_over_arch_when_build_greater`
- [x] `TestLibMambaSolver.test_noarch_preferred_over_arch_when_build_greater_dep`
- [x] `TestLibMambaSolver.test_noarch_preferred_over_arch_when_version_greater`
- [x] `TestLibMambaSolver.test_noarch_preferred_over_arch_when_version_greater_dep`
- [x] `TestLibMambaSolver.test_nonexistent`
- [x] `TestLibMambaSolver.test_nonexistent_deps`
- [x] `TestLibMambaSolver.test_timestamps_and_deps`
- [x] `TestLibMambaSolver.test_unsat_any_two_not_three`
- [x] `TestLibMambaSolver.test_unsat_chain`
- [x] `TestLibMambaSolver.test_unsat_channel_priority`
- [x] `TestLibMambaSolver.test_unsat_expand_single`
- [x] `TestLibMambaSolver.test_unsat_from_r1`
- [x] `TestLibMambaSolver.test_unsat_missing_dep`
- [x] `TestLibMambaSolver.test_unsat_shortest_chain_1`
- [x] `TestLibMambaSolver.test_unsat_shortest_chain_2`
- [x] `TestLibMambaSolver.test_unsat_shortest_chain_3`
- [x] `TestLibMambaSolver.test_unsat_shortest_chain_4`
- [x] `TestLibMambaSolver.test_unsat_simple`
</details>
<details>
<summary><code>tests/testing/test_fixtures.py</code> (0/1 ported)</summary>

- [ ] `test_tmp_channel`
</details>

