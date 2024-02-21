---
layout: home
---

This site provides a collection of [Dash] and [Zeal] docsets, which are generated from the official AWS documentation.
In addition to this website, you can also find these docsets at the [Dash User Contributed Docsets].

Currently only the following docsets are available. If you want to request a new docset, please [open an issue] on GitHub.

[Dash]: https://kapeli.com/dash
[Zeal]: https://zealdocs.org/
[Dash User Contributed Docsets]: https://github.com/Kapeli/Dash-User-Contributions
[open an issue]: https://github.com/tzing/dashify-aws-docs/issues/new

*Disclaimer: The maintainer is not affiliated with AWS.*

## Latest docsets

### ![cloudformation](/assets/CloudFormation.png) [CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)

| Language | Version | Link |
| -------- | ------- | ---- |
{%- for docset_hash in site.data.cloudformation %}
{%- assign docset = docset_hash[1] %}
| {{ docset.lang }} | {{ docset.version }} |       [{{ docset.link | basename }}]({{ docset.link }}) |
{%- endfor %}

### ![redshift](/assets/Redshift.png) [Redshift Database Developer Guide](https://docs.aws.amazon.com/redshift/latest/dg/welcome.html)

| Language | Version | Link |
| -------- | ------- | ---- |
{%- for docset_hash in site.data.redshift %}
{%- assign docset = docset_hash[1] %}
| {{ docset.lang }} | {{ docset.version }} |       [{{ docset.link | basename }}]({{ docset.link }}) |
{%- endfor %}
