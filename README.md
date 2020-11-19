# GSS utils

Shared data transformation utilities for GSS data.

### Known issues

#### vcrpy does not overwrite interactions

When running a test with `record-mode=all` e.g.
```shell script
 pipenv run behave -D record_mode=all --tags=-skip -n '[Name of test]' features/scrape.feature
```
the scrape.yml sections are not overwritten. Instead, new ones are appended.

**Workaround**:
After running the tests, use the `clean-fixtures.py` script to remove repeated interactions.
The run the same tests with `record-mode=none` to confirm they all pass.
```shell script
 pipenv run behave -D record_mode=none --tags=-skip -n '[Name of test]' features/scrape.feature
```

Note, if you run into issues using `clean-fixtures.py` (this can happen as a result of other bad recordings being present) you
can currate the responses for a specific uri as detailed below instead.

#### Currating fixtures for a specific uri

To clean fixtures for a specific uri use `clean-specific-fixture.py` as follow:

To view all recording request/responses for a given uri without modifying anything:
`python3 clean-specific-fixture.py <FULL URI>`

To remove all instances of a specific uri request.responses:
`python3 clean-specific-fixture.py <FULL URI> -clean-all`

To clean all request-response recordings for a specified uri _except_ the one of your choice.

First run `python3 clean-specific-fixture.py <FULL URI>` to get an index for the request/response you want to **keep**, then:
`python3 clean-specific-fixture.py <FULL URI> -clean-but-keep <INDEX_NUMBER>`

---

   Copyright 2018 Alex Tucker

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
