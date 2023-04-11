# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixes

- Fix inconsistent type annotations as reported by mypy
  [#1277](https://github.com/FreeOpcUa/opcua-asyncio/pull/1277)

## [1.0.2] - 2022-04-05

### Added

- allow custom (de)serializer in other namespace than ua
  [#1223](https://github.com/FreeOpcUa/opcua-asyncio/pull/1223)
- Add optional where clause generation to `subscribe_events`
  [#1215](https://github.com/FreeOpcUa/opcua-asyncio/pull/1215)
- Add historizing variable to parse node
  [#1196](https://github.com/FreeOpcUa/opcua-asyncio/pull/1196)
- added the `write` method to `asyncua.client.ua_file`
  [#1126](https://github.com/FreeOpcUa/opcua-asyncio/pull/1126)
- Adds missing method: status_change_notification
  [#1258](https://github.com/FreeOpcUa/opcua-asyncio/pull/1258)


### Changed

- Harding xml import
  [#1259](https://github.com/FreeOpcUa/opcua-asyncio/pull/1259)
- Datatypes: allow optional arrays
  [#1238](https://github.com/FreeOpcUa/opcua-asyncio/pull/1238)
- Handle server cert with clr in create_session
  [#1260](https://github.com/FreeOpcUa/opcua-asyncio/pull/1260)
- Set ServerTimestamp when attributes/values are written
  [#1135](https://github.com/FreeOpcUa/opcua-asyncio/pull/1135)
- Strip Server Certificate from CA
  [#1250](https://github.com/FreeOpcUa/opcua-asyncio/pull/1250)
- tweak default values used fields of ExtensionObject dataclasses
  [#1227](https://github.com/FreeOpcUa/opcua-asyncio/pull/1227)
- ua.uatypes.String used str as base class instead off nothing
  [#1224](https://github.com/FreeOpcUa/opcua-asyncio/pull/1224)
- MethodCall allow None InputArguments
  [#1217](https://github.com/FreeOpcUa/opcua-asyncio/pull/1217)
- Make UaStatusCodeError subclass magic clearer and more concise
  [#1220](https://github.com/FreeOpcUa/opcua-asyncio/pull/1220)
- allow non unicode bytestring nodeid
  [#1216](https://github.com/FreeOpcUa/opcua-asyncio/pull/1216)
- Interpret Null UserIdentityToken as Anonymous during ActivateSession
  [#1173](https://github.com/FreeOpcUa/opcua-asyncio/pull/1173)
- Truncate datetime before 1601-01-01 12:00AM UTC or after 9999-12-31 11:59:59PM UTC
  [#1157](https://github.com/FreeOpcUa/opcua-asyncio/pull/1157)
- Enable usage of certificates that are already loaded into memory
  [#1119](https://github.com/FreeOpcUa/opcua-asyncio/pull/1119)


### Fixes

- Fix publishing in high load situations 
  [#1265](https://github.com/FreeOpcUa/opcua-asyncio/pull/1265)
- Fix MonitoredItemServer._is_data_changed, when as trigger
  ua.DataChangeTrigger.StatusValueTimestamp is used
  [#1253](https://github.com/FreeOpcUa/opcua-asyncio/pull/1253)
- fix monitoritem for mutable values
  [#1243](https://github.com/FreeOpcUa/opcua-asyncio/pull/1243)
- Respect EndpointUrl request parameter in GetEndpoints, FindServers and CreateSession 
  [#1232](https://github.com/FreeOpcUa/opcua-asyncio/pull/1232)
- fix server history save event; init list before use 
  [#1222](https://github.com/FreeOpcUa/opcua-asyncio/pull/1222)
- xmlexporter: fix extensionobjects typeid indentifier missing namespace mapping to idx_in_exported_file
  [#1201](https://github.com/FreeOpcUa/opcua-asyncio/pull/1201)
- make sure we disconnect (in reality kill ThreadLoop) when we get an exception
in `__enter__` in sync wrapper
  [#1218](https://github.com/FreeOpcUa/opcua-asyncio/pull/1218)
- Fix loading a single custom struct
  [#1213](https://github.com/FreeOpcUa/opcua-asyncio/pull/1213)
- Fix/server stop fails when bind fails
  [#1212](https://github.com/FreeOpcUa/opcua-asyncio/pull/1212)
- Fix register server sessionless
  [#1193](https://github.com/FreeOpcUa/opcua-asyncio/pull/1193)
- table names are now validated to prevent sql injection
  [#1186](https://github.com/FreeOpcUa/opcua-asyncio/pull/1186)
- handle missing nodeids in data_type_to_variant_type
  [#1158](https://github.com/FreeOpcUa/opcua-asyncio/pull/1158)
- Don't activate session for unauthorized users
  [#1156](https://github.com/FreeOpcUa/opcua-asyncio/pull/1156)
- Fix off-by-one error in continuation point calculation timestamp
  [#1131](https://github.com/FreeOpcUa/opcua-asyncio/pull/1131)
- Fix the policy-type-annotation in set_security
  [#1112](https://github.com/FreeOpcUa/opcua-asyncio/pull/1112)


## [1.0.1] - 2022-11-07

### Added

- Support python 3.11
  [#1103](https://github.com/FreeOpcUa/opcua-asyncio/pull/1103)


### Fixes
- Respect DataChangeTrigger in server
  [#1099](https://github.com/FreeOpcUa/opcua-asyncio/pull/1099)
- fix some leftovers after rename
  [#1101](https://github.com/FreeOpcUa/opcua-asyncio/pull/1101)
- Only set value to Null if status code is bad
  [#1104](https://github.com/FreeOpcUa/opcua-asyncio/pull/1104)
- AddresSpace fix DataTypes IsAbstract: Default value should be False
  [#1109](https://github.com/FreeOpcUa/opcua-asyncio/pull/1109)
- Ignore SwitchField field in optionsets
  [#1110](https://github.com/FreeOpcUa/opcua-asyncio/pull/1110)
- Fix the policy-type-annotation in set_security
  [#1112](https://github.com/FreeOpcUa/opcua-asyncio/pull/1112)

## [1.0.0] - 2022-10-24

### Added
- add feat: subscription.py optional param for sampling_interval
  [#1087](https://github.com/FreeOpcUa/opcua-asyncio/pull/1087)
  

### Changed

- binary encode/decode recursive structs
  [#1060](https://github.com/FreeOpcUa/opcua-asyncio/pull/1060)
- Client: inform all subscription handler about connection lose
  [#1057](https://github.com/FreeOpcUa/opcua-asyncio/pull/1057)
- Improved exporting and importing extension objects to/from xml
  [#1083](https://github.com/FreeOpcUa/opcua-asyncio/pull/1083)
- Improve naming of parameters in the code
  [#1090](https://github.com/FreeOpcUa/opcua-asyncio/pull/1090)


### Fixes

- Set _closing to False in create_session
  [#1054](https://github.com/FreeOpcUa/opcua-asyncio/pull/1054)
- Added the MaxStringSize parameter to the parser and xml importer
  [#1071](https://github.com/FreeOpcUa/opcua-asyncio/pull/1071)
- Fixes/fix xml import recursive struct
  [#1053](https://github.com/FreeOpcUa/opcua-asyncio/pull/1053)
- Fix typo in in XmlImporte._check_if_namespace_meta_information_is_add ed which
results in an exception
  [#1066](https://github.com/FreeOpcUa/opcua-asyncio/pull/1066)
  

## [0.9.98] - 2022-09-27

### Added

- add Integer and UInteger types
  [#1009](https://github.com/FreeOpcUa/opcua-asyncio/pull/1009)
- enhance nodeset generator: add Windows support and allow targeting a branch
  [#1049](https://github.com/FreeOpcUa/opcua-asyncio/pull/1049)

### Changed 
- review all big exception handlings and try to better follow best practices
  [#1048](https://github.com/FreeOpcUa/opcua-asyncio/pull/1048)
- update schema to v1.05.01 2022-02-24
  [#1047](https://github.com/FreeOpcUa/opcua-asyncio/pull/1047)
- union allow multiple fields with the same type
  [#1042](https://github.com/FreeOpcUa/opcua-asyncio/pull/1042)


### Fixed
- correct 1.04 struct basedatatype
  [#1052](https://github.com/FreeOpcUa/opcua-asyncio/pull/1052)
- server: exit on malformed packet
  [#1046](https://github.com/FreeOpcUa/opcua-asyncio/pull/1046)


## [0.9.97] - 2022-09-21

### Fixed

- Fix regression on connection limits introduced in 0.9.96
  [#1043](https://github.com/FreeOpcUa/opcua-asyncio/pull/1043)

## [0.9.96] - 2022-09-20

### Added

- Client: Add watchdog for connection status
  [#986](https://github.com/FreeOpcUa/opcua-asyncio/pull/986)
- adds security policy Aes128-Sha256-RsaOaep
  [#1032](https://github.com/FreeOpcUa/opcua-asyncio/pull/1032)


### Fixed

- Check limits of messages (CVE-2022-25304)
  [#1040](https://github.com/FreeOpcUa/opcua-asyncio/pull/1040)

- Fix default value of LocalTime field in BaseEvent
  [#1002](https://github.com/FreeOpcUa/opcua-asyncio/pull/1002)
- Fix credentials in server_url by urlquoting username and password
  [#1005](https://github.com/FreeOpcUa/opcua-asyncio/pull/1005)
- Properly close session if `connect` fails in `activate_session`
  [#1001](https://github.com/FreeOpcUa/opcua-asyncio/pull/1001)
- xmlimport change datatype field default 
  [#1008](https://github.com/FreeOpcUa/opcua-asyncio/pull/1008)
- fixed an UnboundLocalError
  [#1012](https://github.com/FreeOpcUa/opcua-asyncio/pull/1012)
- Always check if session is activated
  [#1015](https://github.com/FreeOpcUa/opcua-asyncio/pull/1015)
- Fix interpretation of IncludeSubtypes in Browse requests.
  [#1018](https://github.com/FreeOpcUa/opcua-asyncio/pull/1018)
- Always take NamespaceIndex into account when comparing NodeIds
  [#1017](https://github.com/FreeOpcUa/opcua-asyncio/pull/1017)
- fix Node register
  [#1036](https://github.com/FreeOpcUa/opcua-asyncio/pull/1036)
- server handle malformed packets
  [#1039](https://github.com/FreeOpcUa/opcua-asyncio/pull/1039)


## [0.9.95] - 2022-08-19

### Added
- Add support for pre 1.04 optionsets
  [#900](https://github.com/FreeOpcUa/opcua-asyncio/pull/900)
- Add modeling rule for method arguments
  [#939](https://github.com/FreeOpcUa/opcua-asyncio/pull/939)
- XMLImport - add namespace meta if missing in nodeset
  [#971](https://github.com/FreeOpcUa/opcua-asyncio/pull/971)
- Completion of the Sync api: add some missing methods
  [#975](https://github.com/FreeOpcUa/opcua-asyncio/pull/975)

### Changed 
- Rework struct1_04 resolution
  [#901](https://github.com/FreeOpcUa/opcua-asyncio/pull/901)
- Handle objects in EventTypes. If a EventType has a object as child, add it's
variables and properties to the eventfilter. Also handles variables that contain
nested variables or objects.
  [#906](https://github.com/FreeOpcUa/opcua-asyncio/pull/906)
- XMLExport: make export values optional
  [#923](https://github.com/FreeOpcUa/opcua-asyncio/pull/923)
- Parse all datatype nodes for children
  [#949](https://github.com/FreeOpcUa/opcua-asyncio/pull/949)
- XMLImport relaxed mode: In non strict_mode most errors are just logged an the
import continues.
  [#947](https://github.com/FreeOpcUa/opcua-asyncio/pull/947)
- Speed up eventfilter creation
  [#919](https://github.com/FreeOpcUa/opcua-asyncio/pull/919)

### Fixed

- Fix wrong return type in get_filter_from_event_type
  [#911](https://github.com/FreeOpcUa/opcua-asyncio/pull/911)
- Fix _open_secure_channel_exchange typehints
  [#920](https://github.com/FreeOpcUa/opcua-asyncio/pull/920)
- Fix: Value in DataValue can be optional 
  [#931](https://github.com/FreeOpcUa/opcua-asyncio/pull/931)
- You can now call `activate_session()` without arguments without discarding a
certificate previously set with `load_client_certificate()`.
  [#932](https://github.com/FreeOpcUa/opcua-asyncio/pull/932)
- Use XmlExporter _node_to_string instead of Node.to_string
_node_to_string correctly maps namespaces idxs
  [#948](https://github.com/FreeOpcUa/opcua-asyncio/pull/948)
- Structs104: Fix alias of basetype
  [#954](https://github.com/FreeOpcUa/opcua-asyncio/pull/954)
- Fixed XmlExporter raising BadAttributeIdInvalid on optional fields
  [#951](https://github.com/FreeOpcUa/opcua-asyncio/pull/951)
- Fix XML import bottlenecks
  [#963](https://github.com/FreeOpcUa/opcua-asyncio/pull/963)
- structures104: sort type dependencies correctly
  [#965](https://github.com/FreeOpcUa/opcua-asyncio/pull/965)
- Always close SecureChannel: Fix cases where a secure channel can be leaked
  [#970](https://github.com/FreeOpcUa/opcua-asyncio/pull/970)
- Use correct datatype for EncodingMask
  [#998](https://github.com/FreeOpcUa/opcua-asyncio/pull/998)
- bugfix generating uaprotocol_auto
  [#984](https://github.com/FreeOpcUa/opcua-asyncio/pull/984)


## [0.9.94] - 2022-05-21

### Added
- Add create_subscription to sync server
  [#887](https://github.com/FreeOpcUa/opcua-asyncio/pull/887)

### Fixed

- Fix default value for structs with lists
  [#894](https://github.com/FreeOpcUa/opcua-asyncio/pull/894)
- Fix enum regression 
  [#898](https://github.com/FreeOpcUa/opcua-asyncio/pull/898)
- Set Client locale 
  [#890](https://github.com/FreeOpcUa/opcua-asyncio/pull/890)
