# ZIP Payload Cut Short

`ansible-runner transmit <playbook_dir> -p main.yml` produces the below. That is consumed by `ansible-playbook worker`.
```
{"kwargs": ...}
{"zipfile": 4}
DEADBEEF{"eof": true}
```


`cutoff.py` understands `ansible-runner` protocol. It will send partial zipfile base64 encoded contents, closing the stream early. The size is randomly chosen and is always less than the total size.
```
{"kwargs": ...}
{"zipfile": 4}
DEADBE
```


_What happens if we cut the zip payload `DEADBEEF` short?_

`ansible-runner worker` knows that it wants to read 4 bytes of base 64 _decoded_ data or 8 bytes of base64 _encoded_ data `int(4*((4 + 2) / 3))`. BUT, ansible-runner does NOT make use of that data in the case of where the zip payload comes up short.

`ansible-runner transmit private_data_dir -p main.yml | ./cutoff.py | ansible-runner worker` to see how `ansible-runner worker` responds to a payload that is randomly cut short.

## Errors Found

Errors raised by `ansible-runner worker`

`zipfile.BadZipFile: File is not a zip file` - Payload happened to be a multiple of 4 when it was cut off.

```
$ ansible-runner transmit private_data_dir -p main.yml | ./cutoff.py | ansible-runner worker
{"status": "error", "job_explanation": "Failed to extract private data directory on worker.", "result_traceback": "Traceback (most recent call last):\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/streaming.py\", line 194, in run\n    unstream_dir(self._input, data['zipfile'], self.private_data_dir)\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/utils/streaming.py\", line 78, in unstream_dir\n    with zipfile.ZipFile(tmp.name, \"r\") as archive:\n  File \"/usr/lib64/python3.9/zipfile.py\", line 1268, in __init__\n    self._RealGetContents()\n  File \"/usr/lib64/python3.9/zipfile.py\", line 1335, in _RealGetContents\n    raise BadZipFile(\"File is not a zip file\")\nzipfile.BadZipFile: File is not a zip file\n"}
{"eof": true}
```

`binascii.Error: Invalid base64-encoded string: number of data characters (505) cannot be 1 more than a multiple of 4` - 1 extra bytes. Not enough to be another base64 encoded byte.

```
$ ansible-runner transmit private_data_dir -p main.yml | ./cutoff.py | ansible-runner worker
{"status": "error", "job_explanation": "Failed to extract private data directory on worker.", "result_traceback": "Traceback (most recent call last):\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/streaming.py\", line 194, in run\n    unstream_dir(self._input, data['zipfile'], self.private_data_dir)\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/utils/streaming.py\", line 73, in unstream_dir\n    data = source.read(chunk_size)\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/utils/base64io.py\", line 259, in read\n    results.write(base64.b64decode(data))\n  File \"/usr/lib64/python3.9/base64.py\", line 87, in b64decode\n    return binascii.a2b_base64(s)\nbinascii.Error: Invalid base64-encoded string: number of data characters (505) cannot be 1 more than a multiple of 4\n"}
{"eof": true}
```

`binascii.Error: Incorrect padding` - `FF` for example would trigger this.

```
$ ansible-runner transmit private_data_dir -p main.yml | ./cutoff.py | ansible-runner worker
{"status": "error", "job_explanation": "Failed to extract private data directory on worker.", "result_traceback": "Traceback (most recent call last):\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/streaming.py\", line 194, in run\n    unstream_dir(self._input, data['zipfile'], self.private_data_dir)\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/utils/streaming.py\", line 73, in unstream_dir\n    data = source.read(chunk_size)\n  File \"/home/cmeyers/.local/lib/python3.9/site-packages/ansible_runner/utils/base64io.py\", line 259, in read\n    results.write(base64.b64decode(data))\n  File \"/usr/lib64/python3.9/base64.py\", line 87, in b64decode\n    return binascii.a2b_base64(s)\nbinascii.Error: Incorrect padding\n"}
{"eof": true}
```
