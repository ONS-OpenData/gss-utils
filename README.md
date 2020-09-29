# GSS utils

Shared data transformation utilities for GSS data.

### Known issues

#### vcrpy does not overwrite interactions

When running tests with `record-mode=all` e.g.
```shell script
 pipenv run behave -D record_mode=all --tags=-skip -n 'NHS' features/scrape.feature
```
the scrape.yml sections are not overwritten. Instead, new ones are appended.

**Workaround**:
After running the tests, use the `clean-fixtures.py` script to remove repeated interactions.
The run the same tests with `record-mode=none` to confirm they all pass.
```shell script
 pipenv run behave -D record_mode=none --tags=-skip -n 'NHS' features/scrape.feature
```

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
