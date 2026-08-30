#!/usr/bin/env python3
"""Generate terraform/html/terraform-101.html.

Terraform fundamentals for a reader at absolute zero: no prior Terraform, no HCL, no
AWS. Runs before the AWS primer and before lab00. Self-contained: no CDN, no external
fonts, no raster images. Re-running overwrites the output byte-for-byte.

    python3 curriculum/gen_terraform_101.py
"""

from pathlib import Path

from tf_style import esc, page, topic

OUT = Path(__file__).resolve().parent.parent / "terraform" / "html" / "terraform-101.html"

MANUALS = "../labmanuals"

LAB00 = f"{MANUALS}/lab00-aws-setup-and-init.md"
LAB01 = f"{MANUALS}/lab01-providers-init.md"
LAB04 = f"{MANUALS}/lab04-plan-apply-destroy.md"
LAB05 = f"{MANUALS}/lab05-fmt-validate.md"
LAB08 = f"{MANUALS}/lab08-local-state.md"

TRACK_TF = "&gt;= 1.5.0"
TRACK_AWS = "~&gt; 5.0"
CURRENT_TF = "1.16.0"


# --------------------------------------------------------------------------------------
# local card helpers — composition only, no new CSS, no palette fork
# --------------------------------------------------------------------------------------

def tbl(headers, rows, first_col_width="30%"):
    """A table using the shared styles. First cell of each row gets the lineref style."""
    head = "".join(
        f'<th{f" style=\"width:{first_col_width};\"" if i == 0 else ""}>{h}</th>'
        for i, h in enumerate(headers)
    )
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="lineref">{c}</td>' if i == 0 else f"<td>{c}</td>"
            for i, c in enumerate(row)
        )
        body.append(f"                    <tr>{cells}</tr>")
    return (
        "            <table>\n"
        f"                <thead><tr>{head}</tr></thead>\n"
        "                <tbody>\n" + "\n".join(body) + "\n"
        "                </tbody>\n"
        "            </table>\n"
    )


def card(eyebrow, heading, blocks):
    """A prose card. `blocks` is a list of ready-made HTML strings."""
    inner = "\n".join(blocks)
    return (
        '        <div class="card">\n'
        f'            <span class="eyebrow">{eyebrow}</span>\n'
        f"            <h2>{heading}</h2>\n"
        f"{inner}"
        "        </div>\n"
    )


def p(text):
    return f'            <p class="concept">{text}</p>\n'


def h3(text):
    return f"            <h3>{text}</h3>\n"


def pre(code, output=False):
    cls = ' class="output"' if output else ""
    return f"<pre{cls}>{esc(code)}</pre>\n"


def note(text, warn=False):
    cls = "warn" if warn else "note"
    return f'            <div class="{cls}">{text}</div>\n'


def lablink(href, label):
    return f'            <a class="lablink" href="{href}">Practise it in {label} &rarr;</a>\n'


def c(text):
    """Inline code span. Escapes its own content."""
    return f'<code class="inline">{esc(text)}</code>'


def link(href, label):
    return f'<a class="lablink" style="margin:0;" href="{href}">{label}</a>'


# --------------------------------------------------------------------------------------
# 0 — how to read this page
# --------------------------------------------------------------------------------------

INTRO = card(
    "Start here",
    "Terraform 101 — the page before every other page",
    [
        p(
            "This page assumes you have never run Terraform, never seen a "
            f"{c('.tf')} file, and have no cloud experience. Every term is defined the "
            "first time it appears, and nothing later in the page is assumed earlier. "
            "Read it top to bottom once, then start "
            f"{link(LAB00, 'Lab 00')}."
        ),
        p(
            "Two words are used constantly and are worth pinning down before anything "
            f"else. A <strong>binary</strong> is a single ready-to-run program file; "
            f"{c('terraform')} is one file you download and put on your computer, not an "
            "application you install with a wizard. A <strong>CLI</strong> "
            "(command-line interface) is a program you drive by typing commands into a "
            "terminal instead of clicking buttons. Terraform is a CLI binary."
        ),
        note(
            f"This track targets Terraform <strong>{TRACK_TF}</strong> and the AWS "
            f"provider <strong>{TRACK_AWS}</strong>, in region {c('us-east-2')}. "
            f"Section 9 explains exactly what those two version strings permit."
        ),
    ],
)


# --------------------------------------------------------------------------------------
# 1 — what Terraform is
# --------------------------------------------------------------------------------------

WHAT_IT_IS = card(
    "1 &middot; The idea",
    "What Terraform is",
    [
        p(
            "Terraform is an <strong>infrastructure as code</strong> tool. Infrastructure "
            "means the servers, networks, databases and permissions your software runs on. "
            "Infrastructure as code means you write those things down in text files, keep "
            "the files like any other source code, and let a program build the real thing "
            "from them."
        ),
        p(
            "Terraform is <strong>declarative</strong>: you describe the end result you "
            "want, and the tool works out the steps. The opposite is "
            "<strong>imperative</strong>, where you write the steps yourself and the end "
            "result is whatever the steps happen to produce. A shopping list is "
            "declarative; turn-by-turn driving directions are imperative."
        ),
        h3("The same job, three ways"),
        tbl(
            ["Approach", "How you express it", "What happens on the second run"],
            [
                (
                    "Web console",
                    "You click through forms in a browser to create one server.",
                    "You click through them again, from memory, and get something "
                    "slightly different. Nothing recorded what you did.",
                ),
                (
                    "Shell script",
                    f"You write {c('aws ec2 run-instances ...')} — the exact command to "
                    "create a server. Imperative.",
                    "It creates a <em>second</em> server, because the script says "
                    "&quot;create&quot;, not &quot;make sure one exists&quot;. You must "
                    "hand-write the checks yourself.",
                ),
                (
                    "Terraform",
                    "You write &quot;there is one server, of this size, with these "
                    "tags&quot;. Declarative.",
                    "Nothing happens. Reality already matches the file, so there is "
                    "nothing to do.",
                ),
            ],
            first_col_width="16%",
        ),
        p(
            "That last row is <strong>idempotence</strong>: running the same operation "
            "again produces the same end state instead of stacking up duplicates. It is "
            "the single most useful property Terraform gives you, and it is why the "
            "declarative style is worth learning."
        ),
        h3("A whole Terraform file"),
        pre(
            "# main.tf\n"
            "\n"
            'resource "random_pet" "example" {\n'
            "  length = 2\n"
            "}\n"
        ),
        p(
            "That is a complete, valid configuration. It says: a random two-word name "
            "exists. It does not say how to generate one, when to generate one, or what "
            "to do if one already exists — Terraform decides all of that. The example "
            "deliberately creates nothing in any cloud, so it costs nothing and needs no "
            "account."
        ),
        lablink(LAB04, "Lab 04 — plan, apply, destroy"),
    ],
)


# --------------------------------------------------------------------------------------
# 2 — why anyone uses it
# --------------------------------------------------------------------------------------

WHY = card(
    "2 &middot; The payoff",
    "What it does for you",
    [
        p(
            "Every benefit below follows from one fact: your infrastructure is now a text "
            "file, and text files can be copied, compared, reviewed and deleted."
        ),
        tbl(
            ["Benefit", "What it means in practice"],
            [
                (
                    "Repeatability",
                    "The same files build the same environment in a test account and a "
                    "production account. New joiners run one command instead of "
                    "following a wiki page of screenshots.",
                ),
                (
                    "Review",
                    "A change to a firewall rule arrives as a change to a line of text. A "
                    "colleague can read it, question it and approve it before it reaches "
                    "the real network.",
                ),
                (
                    "Versioning",
                    "The files live in version control, so you can see who changed the "
                    "server size, when, and why, and you can go back to last week's "
                    "definition.",
                ),
                (
                    "Teardown",
                    "One command destroys everything the files created — and only that. "
                    "Manually built environments linger for years because nobody is sure "
                    "what is safe to delete.",
                ),
                (
                    "A dry run",
                    "Terraform can show you exactly what it intends to change before it "
                    "changes anything. No web console offers that.",
                ),
            ],
            first_col_width="18%",
        ),
        note(
            "The dry run is the habit that separates confident Terraform users from "
            "nervous ones. Section 10 introduces the command that produces it."
        ),
    ],
)


# --------------------------------------------------------------------------------------
# 3 — who owns it
# --------------------------------------------------------------------------------------

OWNERSHIP = card(
    "3 &middot; Provenance",
    "Who owns Terraform, and what happened to its licence",
    [
        p(
            "Terraform was created by HashiCorp in 2014. HashiCorp is now a wholly owned "
            "subsidiary of <strong>IBM</strong>: IBM announced the acquisition on 24 April "
            "2024 and completed it on <strong>27 February 2025</strong>, at an enterprise "
            "value of 6.4 billion US dollars. The products kept their names, and the "
            f"{c('terraform')} binary is still published by HashiCorp."
        ),
        h3("The licence change"),
        p(
            "A <strong>licence</strong> is the legal document saying what you are allowed "
            "to do with someone else's code. From its first release up to and including "
            "version 1.5.7, Terraform used the Mozilla Public License 2.0 (MPL 2.0), a "
            "recognised open-source licence with essentially no restrictions on use. On 10 "
            "August 2023 HashiCorp announced that all future releases would move to the "
            "<strong>Business Source License 1.1 (BSL)</strong>. That change took effect "
            "from <strong>Terraform 1.6.0</strong>."
        ),
        p(
            "BSL is <em>source-available</em>, not open-source: you can read and modify the "
            "code, but there is a restriction attached. The restriction is narrow. The "
            "additional use grant in Terraform's licence file permits production use "
            "outright, and only forbids offering Terraform to third parties on a hosted or "
            "embedded basis in a paid product that competes with IBM's own paid Terraform "
            "offerings. It states explicitly that using Terraform for internal purposes "
            "within an organisation is not a competitive offering. Each individual release "
            "reverts to MPL 2.0 four years after it was published."
        ),
        note(
            "<strong>What this means for you on this track:</strong> nothing. Learning "
            "Terraform, running it in a training account, and using it to manage your own "
            "employer's infrastructure are all permitted without payment. The restriction "
            "only bites if you sell a competing Terraform-based service."
        ),
        h3("Why OpenTofu exists"),
        p(
            "The licence change was unpopular with users who had built businesses around "
            "the previously open-source code. A group of companies and individuals "
            "published a manifesto asking for the change to be reverted; when it was not, "
            "they <strong>forked</strong> the project — took a copy of the last MPL 2.0 "
            "release, 1.5.7, and continued it independently. That fork is "
            "<strong>OpenTofu</strong>, accepted by the Linux Foundation on 20 September "
            "2023, with OpenTofu 1.6 shipping in January 2024 as a drop-in replacement for "
            "Terraform 1.6."
        ),
        p(
            "OpenTofu is a separate project today with its own release schedule and some "
            "features Terraform does not have, but it still uses the same configuration "
            f"language and the same state file format, and its command is {c('tofu')} "
            f"instead of {c('terraform')}. Most material written for Terraform 1.x applies "
            "to it unchanged. <strong>This track teaches Terraform</strong>, so every "
            f"command on these pages starts with {c('terraform')}. You will hear the name "
            "OpenTofu; now you know what it is."
        ),
        h3("Verify these facts yourself"),
        tbl(
            ["Claim", "Primary source"],
            [
                (
                    "IBM completed the acquisition on 27 Feb 2025",
                    link(
                        "https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp,-creates-comprehensive,-end-to-end-hybrid-cloud-platform",
                        "IBM newsroom announcement",
                    ),
                ),
                (
                    "BSL 1.1 applies from Terraform 1.6.0; licensor is IBM",
                    link(
                        "https://github.com/hashicorp/terraform/blob/main/LICENSE",
                        "hashicorp/terraform LICENSE",
                    ),
                ),
                (
                    "Licence interpretation guidance",
                    link("https://www.hashicorp.com/license-faq", "HashiCorp licence FAQ"),
                ),
                (
                    "OpenTofu, the fork of Terraform 1.5.7",
                    link("https://opentofu.org/", "opentofu.org"),
                ),
            ],
            first_col_width="42%",
        ),
    ],
)


# --------------------------------------------------------------------------------------
# 4 — versions
# --------------------------------------------------------------------------------------

VERSIONS = card(
    "4 &middot; Versions",
    "Terraform version numbers, and which one this track wants",
    [
        p(
            "Terraform version numbers have three parts separated by dots — "
            f"{c('MAJOR.MINOR.PATCH')}, for example {c('1.16.0')}. This is the "
            "<strong>semantic versioning</strong> convention: the major number changes when "
            "something old stops working, the minor number changes when features are added, "
            "and the patch number changes for bug fixes only."
        ),
        p(
            "Terraform reached 1.0 in June 2021 and has stayed on major version 1 ever "
            "since, with a promise that configuration written for one 1.x release keeps "
            "working on later 1.x releases. In practice that means the gap between your "
            "version and this track's floor rarely matters, as long as yours is newer."
        ),
        h3("Ask your own installation"),
        pre("terraform version"),
        h3("Expected output"),
        pre(
            "Terraform v1.14.8\n"
            "on darwin_arm64\n"
            "\n"
            "Your version of Terraform is out of date! The latest version\n"
            "is 1.16.0.\n",
            output=True,
        ),
        p(
            "The first line is your installed version. The second is the operating system "
            "and processor architecture the binary was built for. The third line appears "
            "only when a newer release exists — Terraform checks the public release index "
            "when you run this command."
        ),
        tbl(
            ["Version", "Status"],
            [
                (
                    f"{CURRENT_TF}",
                    "The current release at the time this page was generated, published 26 "
                    "August 2026. Verified against "
                    + link(
                        "https://developer.hashicorp.com/terraform/install",
                        "developer.hashicorp.com/terraform/install",
                    )
                    + ".",
                ),
                (
                    "1.5.7",
                    "The last MPL 2.0 release, and the point OpenTofu forked from. Also the "
                    "last release before this track's floor.",
                ),
                (
                    TRACK_TF,
                    "<strong>What this track requires.</strong> Every lab is written "
                    "against this floor. Anything from 1.5.0 upwards, including the current "
                    "release, will work.",
                ),
            ],
            first_col_width="18%",
        ),
        note(
            "If your version is older than 1.5.0, download a newer one before Lab 00. If it "
            "is newer than 1.16.0 by the time you read this, that is fine — the floor is a "
            "minimum, not a target."
        ),
        lablink(LAB00, "Lab 00 — AWS setup and init"),
    ],
)


# --------------------------------------------------------------------------------------
# 5 — what HCL is (block anatomy)
# --------------------------------------------------------------------------------------

HCL_CODE = """resource "aws_instance" "web" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.micro"

  tags = {
    Name = "tflabs-web"
    Lab  = "lab03"
  }
}"""

HCL_ROWS = [
    (
        "<code>resource</code>",
        "The <strong>block type</strong>. It says what kind of thing this block declares. "
        "Terraform has a fixed set of block types: <code>resource</code>, <code>data</code>, "
        "<code>variable</code>, <code>output</code>, <code>provider</code>, "
        "<code>terraform</code>, <code>locals</code>, <code>module</code>.",
    ),
    (
        "<code>&quot;aws_instance&quot;</code>",
        "The first <strong>block label</strong>. For a resource block this is the resource "
        "type — the exact kind of real-world thing to create. The name is fixed by the "
        "provider, so you cannot invent it.",
    ),
    (
        "<code>&quot;web&quot;</code>",
        "The second block label: the <strong>local name</strong>. You choose this freely. It "
        "is how you refer to this block elsewhere in your own configuration, and it never "
        "appears in AWS.",
    ),
    (
        "<code>{ ... }</code>",
        "The <strong>body</strong>: everything between the braces. It holds arguments and "
        "sometimes nested blocks.",
    ),
    (
        "<code>instance_type</code>",
        "An <strong>argument name</strong>. Which arguments are valid, and which are "
        "required, is decided by the resource type.",
    ),
    (
        "<code>&quot;t3.micro&quot;</code>",
        "An <strong>argument value</strong>. Here a literal piece of text in double quotes.",
    ),
    (
        "<code>data.aws_ami.al2023.id</code>",
        "Also an argument value, but an <strong>expression</strong> rather than a literal: "
        "it reads a value out of another block instead of stating one. Sections 6 and 7 "
        "cover expressions and <code>data</code> blocks.",
    ),
    (
        "<code>tags</code>",
        "An argument whose value is a group of key/value pairs in braces. Nesting is normal "
        "in HCL and the indentation is purely for humans.",
    ),
]

HCL = topic(
    "5 &middot; The language",
    "What HCL is, and the anatomy of a block",
    "<strong>HCL</strong> is the HashiCorp Configuration Language — the language you write "
    "Terraform in. You put it in plain text files whose names end in "
    f"{c('.tf')}, and Terraform reads <em>every</em> {c('.tf')} file in the directory you run "
    "it from and treats them as one configuration. File names carry no meaning to Terraform; "
    f"{c('main.tf')} is a convention, not a rule. HCL is built from just two things: "
    "<strong>blocks</strong>, which are named containers written with braces, and "
    "<strong>arguments</strong>, which are name-equals-value pairs inside them. The example "
    "below is one block, and the table names every part of it.",
    esc(HCL_CODE),
    HCL_ROWS,
    lang_note=(
        "<strong>How the parts become an address.</strong> The two labels combine into a "
        f"<strong>reference address</strong> you use to point at this block from anywhere "
        f"else: {c('aws_instance.web.id')} means resource type {c('aws_instance')}, local name "
        f"{c('web')}, attribute {c('id')} — the instance ID that AWS assigns after creation. "
        f"Blocks declared with {c('data')} instead of {c('resource')} take a {c('data.')} "
        f"prefix, which is why the AMI above is {c('data.aws_ami.al2023.id')} and not "
        f"{c('aws_ami.al2023.id')}."
    ),
    lab_href=LAB01,
    lab_label="Lab 01 — providers and init",
)


# --------------------------------------------------------------------------------------
# 6 — HCL language basics
# --------------------------------------------------------------------------------------

BASICS_CODE = """# A comment starts with a hash. // also works for one line,
/* and this form spans
   several lines. */

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "dev"
}

locals {
  instance_count = 2                            # number
  enable_logging = true                         # bool
  zones          = ["us-east-2a", "us-east-2b"] # list of string

  # map of string
  common_tags = {
    Project = "tflabs"
    Env     = var.environment
  }

  name_prefix = "tflabs-${var.environment}-web" # interpolation: needed
  env_name    = var.environment                 # no interpolation: not needed
}"""

BASICS_ROWS = [
    (
        "<code>#</code> <code>//</code> <code>/* */</code>",
        "The three comment forms. Terraform ignores them. <code>#</code> is the conventional "
        "one and <code>terraform fmt</code> rewrites <code>//</code> to <code>#</code>.",
    ),
    (
        "<code>type = string</code>",
        "A <strong>string</strong> is text in double quotes. Declaring the type makes "
        "Terraform reject a wrong value early with a clear error instead of a confusing one "
        "later.",
    ),
    (
        "<code>2</code>",
        "A <strong>number</strong>. Written bare, with no quotes. <code>&quot;2&quot;</code> "
        "would be a string that happens to contain a digit.",
    ),
    (
        "<code>true</code>",
        "A <strong>bool</strong> — either <code>true</code> or <code>false</code>, lower "
        "case, no quotes.",
    ),
    (
        "<code>[ ... ]</code>",
        "A <strong>list</strong>: ordered values in square brackets, reached by position "
        "starting at zero, so <code>local.zones[0]</code> is "
        "<code>&quot;us-east-2a&quot;</code>.",
    ),
    (
        "<code>{ ... }</code>",
        "A <strong>map</strong>: values reached by key rather than position, so "
        "<code>local.common_tags[&quot;Project&quot;]</code> is "
        "<code>&quot;tflabs&quot;</code>. An <strong>object</strong> is the same shape with a "
        "fixed set of keys whose types are declared individually.",
    ),
    (
        "<code>var.environment</code>",
        "A <strong>reference</strong>. The address form is source, then name, then attribute: "
        "<code>var.NAME</code> for a variable, <code>local.NAME</code> for a local value, "
        "<code>RESOURCE_TYPE.NAME.ATTRIBUTE</code> for a resource.",
    ),
    (
        "<code>&quot;tflabs-${var.environment}-web&quot;</code>",
        "<strong>Interpolation</strong>: <code>${ }</code> inside a quoted string means "
        "&quot;evaluate this and paste the result here&quot;. Needed here because the value "
        "is glued between two pieces of literal text.",
    ),
    (
        "<code>= var.environment</code>",
        "The same value with <strong>no</strong> interpolation, because it is the whole "
        "value. Writing <code>&quot;${var.environment}&quot;</code> would work but is "
        "redundant, and Terraform warns about it.",
    ),
]

BASICS = topic(
    "6 &middot; The language",
    "HCL basics: types, comments, references and formatting",
    "Every argument value in HCL has a <strong>type</strong>. There are three simple types — "
    "string, number and bool — and three collection types — list, map and object. You will "
    "also write <strong>expressions</strong>: values computed from other values rather than "
    "typed out literally. Two blocks below are new: "
    f"{c('variable')} declares an input someone can set from outside, and {c('locals')} names "
    "values used repeatedly inside the configuration. Both are covered properly later in the "
    "track; here they are just convenient places to show the types.",
    esc(BASICS_CODE),
    BASICS_ROWS,
    lang_note=(
        f"<strong>Formatting is automatic.</strong> The {c('=')} signs above line up in "
        "columns. Nobody does that by hand — running "
        f"{c('terraform fmt')} rewrites every {c('.tf')} file in the directory to the "
        "canonical style: standard indentation, aligned equals signs, consistent comment "
        f"markers. It changes layout only, never meaning. Run it before every commit, and "
        f"use {c('terraform fmt -check')} in automation to fail a build that was not "
        "formatted."
    ),
    lab_href=LAB05,
    lab_label="Lab 05 — fmt and validate",
)


# --------------------------------------------------------------------------------------
# 7 — what a provider is
# --------------------------------------------------------------------------------------

PROVIDERS = card(
    "7 &middot; Plugins",
    "What a provider is",
    [
        p(
            "Terraform itself knows nothing about AWS. It does not know what an EC2 instance "
            "is, which API endpoint creates one, or how to authenticate. All of that lives "
            "in a <strong>provider</strong>."
        ),
        p(
            "A provider is a <strong>plugin</strong> — a separate program that Terraform "
            "downloads and runs alongside itself to add a capability it does not have "
            "built in. Each provider translates your HCL into calls against one specific "
            f"API. The {c('aws')} provider defines the resource types whose names begin "
            f"{c('aws_')}; the {c('random')} provider defines {c('random_pet')} and its "
            "siblings and talks to no API at all. There are thousands of others."
        ),
        h3("Where providers come from"),
        p(
            "The <strong>Terraform Registry</strong> at "
            + link("https://registry.terraform.io/", "registry.terraform.io")
            + " is the public catalogue Terraform downloads providers from. Every provider "
            "has a two-part source address, "
            f"{c('NAMESPACE/NAME')}. In {c('hashicorp/aws')}, {c('hashicorp')} is the "
            f"namespace — the organisation that publishes it — and {c('aws')} is the "
            "provider name. The namespace matters: it is what distinguishes the official "
            "AWS provider from a third party's fork of it. The registry is also where the "
            "documentation for every resource type lives, and it is the reference you will "
            "use most often once you start writing real configurations."
        ),
        h3("Where the plugin lands on your disk"),
        p(
            f"You never download a provider by hand. The {c('terraform init')} command reads "
            "your configuration, works out which providers it needs, fetches them, and "
            f"unpacks them into a hidden {c('.terraform')} directory next to your "
            f"{c('.tf')} files:"
        ),
        pre(
            ".terraform/\n"
            "└── providers/\n"
            "    └── registry.terraform.io/\n"
            "        └── hashicorp/\n"
            "            └── aws/\n"
            "                └── 5.31.0/\n"
            "                    └── darwin_arm64/\n"
            "                        └── terraform-provider-aws_v5.31.0_x5\n"
        ),
        p(
            "That last file is the provider binary. The path records the registry it came "
            "from, the namespace, the name, the exact version and the platform it was built "
            f"for. The whole {c('.terraform')} directory is disposable — it is rebuilt by "
            f"{c('terraform init')} and is never committed to version control, because it "
            "contains large platform-specific binaries rather than anything you wrote."
        ),
        note(
            f"Provider version numbers are independent of Terraform's. AWS provider 5.31.0 "
            f"has nothing to do with Terraform {CURRENT_TF}; they are different pieces of "
            "software on different release schedules."
        ),
        lablink(LAB01, "Lab 01 — providers and init"),
    ],
)


# --------------------------------------------------------------------------------------
# 8 — how to add a provider
# --------------------------------------------------------------------------------------

ADD_CODE = """terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}"""

ADD_ROWS = [
    (
        "<code>terraform { }</code>",
        "A block that configures Terraform itself rather than any infrastructure. It takes no "
        "labels, and a configuration has at most one of them.",
    ),
    (
        "<code>required_version</code>",
        "The versions of the <strong>Terraform CLI</strong> this configuration accepts. "
        "Terraform checks its own version against this and refuses to run if it does not "
        "match. It cannot upgrade itself.",
    ),
    (
        "<code>required_providers</code>",
        "The <strong>declaration</strong> block: which plugins this configuration needs, "
        "where to get them, and which versions are acceptable.",
    ),
    (
        "<code>aws = { ... }</code>",
        "The <strong>local name</strong> for this provider inside your configuration. It is "
        "what makes <code>aws_instance</code> resolve to this provider.",
    ),
    (
        "<code>source</code>",
        "The registry address, <code>NAMESPACE/NAME</code>. "
        "<code>&quot;hashicorp/aws&quot;</code> is the official AWS provider. Omitting "
        "<code>source</code> is a bug waiting to happen; always state it.",
    ),
    (
        "<code>version = &quot;~&gt; 5.0&quot;</code>",
        "A <strong>version constraint</strong>: a rule saying which releases are acceptable. "
        "This one accepts any 5.x release — 5.0.1, 5.31.0, 5.99.0 — and refuses 6.0.0 and "
        "newer, and anything older than 5.0. Section 9 decodes every operator in full.",
    ),
    (
        "<code>provider &quot;aws&quot;</code>",
        "The <strong>configuration</strong> block: settings passed to the plugin once it is "
        "installed. Its label matches the local name declared above.",
    ),
    (
        "<code>region</code>",
        "An AWS-provider-specific setting. Every AWS resource in this configuration is "
        "created in <code>us-east-2</code>. Different providers take completely different "
        "settings.",
    ),
]

ADD_PROVIDER = topic(
    "8 &middot; Plugins",
    "How to add a provider, and why it takes two blocks",
    "Adding a provider is always two separate declarations, and beginners reliably confuse "
    f"them. The {c('required_providers')} entry says <em>which plugin to install and which "
    f"versions are acceptable</em>. The {c('provider')} block says <em>how to configure the "
    "plugin once it is installed</em>. They are separate because they answer different "
    "questions at different times: Terraform must resolve and download the plugin before it "
    "can hand it any settings, and a configuration can install one plugin but configure it "
    "several times over — one AWS provider, configured for two regions, is a normal thing to "
    "want. Put both in a file and run "
    f"{c('terraform init')} to make it real.",
    esc(ADD_CODE),
    ADD_ROWS,
    lang_note=(
        f"The {c('terraform')} block is the one place where you cannot use variables or "
        "expressions. Its contents must be literal values, because Terraform reads it before "
        "it has evaluated anything else."
    ),
    lab_href=LAB01,
    lab_label="Lab 01 — providers and init",
)


# --------------------------------------------------------------------------------------
# 9 — version constraint operators
# --------------------------------------------------------------------------------------

CONSTRAINT_ROWS = [
    (
        "<code>= 5.31.0</code><br><code>5.31.0</code>",
        "Exactly one version. The operator is optional, so the bare number means the same "
        "thing. This is the only form that cannot be combined with other conditions, and the "
        "only form that will select a pre-release such as "
        "<code>6.0.0-beta1</code>.",
        "<strong>Allows:</strong> 5.31.0 only.<br>"
        "<strong>Excludes:</strong> everything else, including 5.31.1 and 5.30.9.",
    ),
    (
        "<code>!= 5.31.0</code>",
        "Excludes one exact version. Used to skip a single known-bad release while staying "
        "open to the rest. Almost always paired with another condition.",
        "<strong>Allows:</strong> 5.30.9, 5.31.1, 6.0.0 — every published version except one."
        "<br><strong>Excludes:</strong> 5.31.0.",
    ),
    (
        "<code>&gt; 5.31.0</code>",
        "Strictly newer than the stated version.",
        "<strong>Allows:</strong> 5.31.1, 5.32.0, 6.0.0, 7.4.2.<br>"
        "<strong>Excludes:</strong> 5.31.0 itself, and anything older.",
    ),
    (
        "<code>&gt;= 5.31.0</code>",
        "The stated version or newer. The usual choice for a shared module, which should set "
        "a floor but not a ceiling.",
        "<strong>Allows:</strong> 5.31.0, 5.31.1, 6.0.0, 7.4.2.<br>"
        "<strong>Excludes:</strong> 5.30.9 and anything older.",
    ),
    (
        "<code>&lt; 6.0.0</code>",
        "Strictly older than the stated version. A ceiling, normally used to stay off a major "
        "release that contains breaking changes.",
        "<strong>Allows:</strong> 5.99.0, 5.31.0, 1.0.0.<br>"
        "<strong>Excludes:</strong> 6.0.0 itself, and anything newer.",
    ),
    (
        "<code>&lt;= 6.0.0</code>",
        "The stated version or older.",
        "<strong>Allows:</strong> 6.0.0, 5.99.0, 5.31.0.<br>"
        "<strong>Excludes:</strong> 6.0.1 and anything newer.",
    ),
    (
        "<code>~&gt; 5.0</code>",
        "The <strong>pessimistic constraint</strong>. It allows the right-most component you "
        "wrote to increase, and nothing to its left. You wrote two components, so the "
        "right-most is the <em>minor</em> number: minor and patch may both rise, major may "
        "not.",
        "<strong>Allows:</strong> 5.0.0, 5.0.1, 5.1.0, 5.31.0, 5.99.9 — any 5.x.<br>"
        "<strong>Excludes:</strong> 6.0.0 and newer; 4.67.0 and older.",
    ),
    (
        "<code>~&gt; 5.1.2</code>",
        "The same operator with three components, which means something genuinely different. "
        "The right-most is now the <em>patch</em> number, so only the patch may rise. This is "
        "the form to use when you want bug fixes and nothing else.",
        "<strong>Allows:</strong> 5.1.2, 5.1.3, 5.1.9, 5.1.40.<br>"
        "<strong>Excludes:</strong> 5.2.0 (minor rose), 5.1.1 (older), 6.0.0.",
    ),
    (
        "<code>&gt;= 5.20.0, &lt; 6.0.0</code>",
        "A <strong>compound constraint</strong>: several conditions in one string, separated "
        "by commas. A version must satisfy <em>all</em> of them. This is how you express a "
        "range that no single operator can.",
        "<strong>Allows:</strong> 5.20.0, 5.31.0, 5.99.9.<br>"
        "<strong>Excludes:</strong> 5.19.9, 6.0.0, 6.1.0.",
    ),
    (
        "<code>&gt;= 5.0.0, != 5.31.0, &lt; 6.0.0</code>",
        "Three conditions at once — a floor, a ceiling, and one bad release cut out of the "
        "middle. There is no limit on how many you combine.",
        "<strong>Allows:</strong> 5.0.0, 5.30.9, 5.31.1, 5.99.9.<br>"
        "<strong>Excludes:</strong> 4.99.0, 5.31.0, 6.0.0.",
    ),
]

CONSTRAINTS = card(
    "9 &middot; Version constraints",
    "Every version constraint operator, and what each one really allows",
    [
        p(
            "A <strong>version constraint</strong> is a string that says which releases of "
            "something are acceptable. The same syntax is used in three places: "
            f"{c('required_version')} for Terraform itself, the {c('version')} argument "
            f"inside {c('required_providers')} for a plugin, and the {c('version')} argument "
            "on a module. Learn it once and it applies everywhere."
        ),
        p(
            "The syntax is an operator, a space, and a version number. Terraform installs the "
            "<strong>newest</strong> published version that satisfies every constraint that "
            "applies. If no published version satisfies them, it stops with an error rather "
            "than guessing."
        ),
        tbl(
            ["Constraint", "What the operator means", "Exactly which versions"],
            CONSTRAINT_ROWS,
            first_col_width="20%",
        ),
        note(
            "<strong>Pre-releases are special.</strong> A version with a dash suffix, such as "
            f"{c('6.0.0-beta1')}, is never matched by {c('>')}, {c('>=')}, {c('<')}, "
            f"{c('<=')} or {c('~>')}. To use one you must name it exactly with "
            f"{c('=')} or with no operator at all. This is why {c('>= 5.0.0')} will not "
            "quietly drag a beta into your build."
        ),
        h3("Two different things get versioned, and they are not the same"),
        tbl(
            ["Setting", "Constrains", "If the constraint is not met"],
            [
                (
                    "<code>required_version</code>",
                    "The <strong>Terraform CLI binary</strong> on the machine running the "
                    "command. One per configuration, inside the <code>terraform</code> "
                    "block.",
                    "Terraform refuses to run and tells you to change your Terraform "
                    "installation. It cannot fix this itself — you download a different "
                    "binary.",
                ),
                (
                    "<code>version</code> in <code>required_providers</code>",
                    "A <strong>provider plugin</strong>. One per provider. Completely "
                    "independent of the Terraform version.",
                    "<code>terraform init</code> downloads a version that does satisfy it. "
                    "Terraform fixes this itself, automatically.",
                ),
            ],
            first_col_width="26%",
        ),
        h3("What the constraint permits, and what the lock file pins"),
        p(
            "A constraint describes a <em>range</em>. It does not decide anything on its own. "
            f"The decision is recorded in a file called {c('.terraform.lock.hcl')}, which "
            f"{c('terraform init')} creates in your working directory the first time it "
            "installs a provider."
        ),
        pre(
            "# .terraform.lock.hcl  (generated by terraform init - do not hand-edit)\n"
            '\n'
            'provider "registry.terraform.io/hashicorp/aws" {\n'
            '  version     = "5.31.0"\n'
            '  constraints = "~> 5.0"\n'
            "  hashes = [\n"
            '    "h1:cIUS0MSHV3JQyDb1UDXWvVHmp0IuZ8y7WPMSVJvhBg8=",\n'
            "  ]\n"
            "}\n"
        ),
        tbl(
            ["Line", "What it records"],
            [
                (
                    "<code>version</code>",
                    "The one exact release Terraform actually chose. This is the pin.",
                ),
                (
                    "<code>constraints</code>",
                    "A copy of what your configuration asked for, kept so you can see why "
                    "that version was chosen.",
                ),
                (
                    "<code>hashes</code>",
                    "Checksums of the downloaded package. On later runs Terraform verifies "
                    "the file it fetched matches, so a tampered or substituted plugin fails "
                    "loudly.",
                ),
            ],
            first_col_width="18%",
        ),
        p(
            f"Once a version is recorded, {c('terraform init')} re-selects <em>that</em> "
            "version on every subsequent run, even when a newer one exists inside the "
            f"constraint. The only way to move it is {c('terraform init -upgrade')}, which "
            "discards the recorded selection and picks the newest version the constraint "
            "still allows. Commit the lock file to version control: it is the difference "
            "between everyone on the team running the same plugin and everyone running "
            "whatever was newest on the day they cloned."
        ),
        note(
            "<strong>Why a colleague got a different provider version from the same "
            f"repository.</strong> You cloned in March, ran {c('terraform init')} against "
            f"{c('version = \"~> 5.0\"')}, and got 5.31.0. Your colleague cloned "
            "in September and got 5.94.0. Both are correct: the constraint permits every "
            "5.x, and each of you took the newest available on your own day. The lock file "
            "is what removes the ambiguity — if you had committed it, their "
            f"{c('terraform init')} would have installed 5.31.0 too. A constraint permits a "
            "range; the lock file records the choice."
        ),
        note(
            f"The lock file covers providers only. It does <strong>not</strong> pin the "
            f"Terraform CLI version, and it does not pin module versions — Terraform always "
            "takes the newest module version the constraint allows.",
            warn=True,
        ),
        lablink(LAB01, "Lab 01 — providers and init"),
    ],
)


# --------------------------------------------------------------------------------------
# 10 — the command line
# --------------------------------------------------------------------------------------

COMMANDS = card(
    "10 &middot; The command line",
    "The commands you will actually type",
    [
        p(
            "Terraform is one binary with subcommands. You run them from inside the "
            f"directory that holds your {c('.tf')} files, in roughly the order below. The "
            "first three are safe — they change nothing in any cloud."
        ),
        tbl(
            ["Command", "What it does"],
            [
                (
                    "<code>terraform init</code>",
                    "Prepares the directory: reads your configuration, downloads the "
                    "providers it needs, and writes the lock file. Run it first, and again "
                    "any time you add or change a provider.",
                ),
                (
                    "<code>terraform fmt</code>",
                    "Rewrites your files into the canonical layout. Changes formatting only.",
                ),
                (
                    "<code>terraform validate</code>",
                    "Checks the configuration is internally consistent — no syntax errors, no "
                    "unknown arguments, no references to blocks that do not exist. It does "
                    "not contact any cloud, so it cannot tell you whether AWS will accept "
                    "the request.",
                ),
                (
                    "<code>terraform plan</code>",
                    "The dry run. Compares what you asked for against what exists and prints "
                    "the changes it <em>would</em> make. Changes nothing.",
                ),
                (
                    "<code>terraform apply</code>",
                    "Makes the changes. Shows the same plan first and waits for you to type "
                    "<code>yes</code>. This is the command that creates real, billable "
                    "resources.",
                ),
                (
                    "<code>terraform destroy</code>",
                    "Deletes everything this configuration created. Also asks for "
                    "confirmation. Run it at the end of every lab so nothing keeps costing "
                    "money.",
                ),
                (
                    "<code>terraform output</code>",
                    "Prints the values the configuration chose to publish, such as a server's "
                    "public address.",
                ),
                (
                    "<code>terraform show</code>",
                    "Prints everything Terraform currently knows about what it manages, in "
                    "readable form.",
                ),
                (
                    "<code>terraform state list</code>",
                    "Lists the addresses of everything Terraform is tracking, one per line — "
                    "the quickest way to see what a configuration owns.",
                ),
                (
                    "<code>terraform console</code>",
                    "An interactive prompt for trying out expressions against your real "
                    "values. Type an expression, see what it evaluates to, change nothing.",
                ),
            ],
            first_col_width="24%",
        ),
        h3("Reading a plan: the four symbols"),
        p(
            f"{c('terraform plan')} marks every proposed change with a symbol in the left "
            "margin. Four symbols cover everything you will see, and they are worth learning "
            "now because the rest of this page uses them."
        ),
        tbl(
            ["Symbol", "Meaning", "Why it happens"],
            [
                (
                    "<code>+</code>",
                    "<strong>create</strong>",
                    "The resource is in your configuration but does not exist yet.",
                ),
                (
                    "<code>-</code>",
                    "<strong>destroy</strong>",
                    "The resource exists but you removed it from your configuration.",
                ),
                (
                    "<code>~</code>",
                    "<strong>update in place</strong>",
                    "The resource exists but one of its settings differs. The change can be "
                    "made without deleting anything — for example editing a tag.",
                ),
                (
                    "<code>-/+</code>",
                    "<strong>replace</strong>",
                    "A setting differs that cannot be changed on a live resource, so "
                    "Terraform must destroy it and create a new one. Changing an EC2 "
                    "instance's <code>ami</code> does this. Read these carefully — the old "
                    "resource and anything on it is gone.",
                ),
            ],
            first_col_width="12%",
        ),
        note(
            f"The last line of every plan is a count: "
            f"{c('Plan: 1 to add, 0 to change, 0 to destroy.')} If that line surprises you, "
            f"do not type {c('yes')}."
        ),
        lablink(LAB04, "Lab 04 — plan, apply, destroy"),
    ],
)


# --------------------------------------------------------------------------------------
# 11 — state
# --------------------------------------------------------------------------------------

STATE = card(
    "11 &middot; State",
    "What state is, and why Terraform cannot work without it",
    [
        p(
            "Your configuration says a server should exist. AWS says a server with ID "
            f"{c('i-0a1b2c3d4e5f6a7b8')} exists. Nothing so far connects the two. Terraform "
            f"needs a record saying &quot;the block I call {c('aws_instance.web')} is that "
            "specific machine&quot;. That record is the <strong>state</strong>."
        ),
        p(
            "By default it is a single file in your working directory called "
            f"{c('terraform.tfstate')}, written in JSON. Terraform creates it on the first "
            f"{c('terraform apply')} and updates it on every run afterwards."
        ),
        h3("What it looks like inside"),
        pre(
            "{\n"
            '  "version": 4,\n'
            '  "terraform_version": "1.14.8",\n'
            '  "serial": 3,\n'
            '  "resources": [\n'
            "    {\n"
            '      "mode": "managed",\n'
            '      "type": "aws_instance",\n'
            '      "name": "web",\n'
            '      "instances": [\n'
            "        {\n"
            '          "attributes": {\n'
            '            "id": "i-0a1b2c3d4e5f6a7b8",\n'
            '            "instance_type": "t3.micro",\n'
            '            "tags": { "Name": "tflabs-web", "Lab": "lab03" }\n'
            "          }\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
        ),
        tbl(
            ["Field", "What it is for"],
            [
                (
                    "<code>type</code> + <code>name</code>",
                    "The two labels from your <code>resource</code> block. Together they form "
                    "the address <code>aws_instance.web</code>.",
                ),
                (
                    "<code>id</code>",
                    "The real identifier AWS assigned. This is the link between your text "
                    "file and the running machine.",
                ),
                (
                    "<code>attributes</code>",
                    "Everything Terraform knew about the resource at the end of the last run "
                    "— both what you set and what AWS filled in.",
                ),
                (
                    "<code>serial</code>",
                    "Increments on every write. Used to detect two people writing the same "
                    "state at once.",
                ),
            ],
            first_col_width="24%",
        ),
        h3("Three consequences you need to know now"),
        tbl(
            ["Consequence", "Detail"],
            [
                (
                    "State is the source of identity",
                    "Delete the state file and Terraform forgets it ever built anything. Your "
                    "next <code>plan</code> shows <code>+</code> for everything and "
                    "<code>apply</code> builds a second copy, while the first keeps running "
                    "and billing. Back it up; never delete it to &quot;start clean&quot;.",
                ),
                (
                    "State holds secrets in plaintext",
                    "<strong>Plaintext</strong> means readable text with no encryption. If a "
                    "resource has a generated database password, that password is sitting in "
                    "<code>terraform.tfstate</code> in readable form, even if you marked the "
                    "variable sensitive. Never commit a state file to git and never put one "
                    "in a public bucket.",
                ),
                (
                    "Local state is single-player",
                    "The default file lives on your laptop, so nobody else can see it. Two "
                    "people running <code>apply</code> against the same infrastructure from "
                    "two laptops will corrupt each other's work. Teams therefore move state "
                    "to a shared <strong>remote backend</strong> — a bucket or service that "
                    "holds one copy for everyone and locks it during a run. The advanced "
                    "tier of this track covers that; the basic and intermediate labs all use "
                    "local state, which is correct for one person learning alone.",
                ),
            ],
            first_col_width="24%",
        ),
        note(
            f"State is Terraform's memory of the last run, not a live view of AWS. Keeping "
            f"the two in agreement is the whole subject of the next section.",
        ),
        lablink(LAB08, "Lab 08 — local state"),
    ],
)


# --------------------------------------------------------------------------------------
# 12 — drift
# --------------------------------------------------------------------------------------

DRIFT_TF = """resource "aws_instance" "web" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.micro"

  tags = {
    Name = "tflabs-web"
    Lab  = "lab03"
  }
}"""

DRIFT_PLAN = """aws_instance.web: Refreshing state... [id=i-0a1b2c3d4e5f6a7b8]

Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the
last "terraform apply" which may have affected this plan:

  # aws_instance.web has been changed
  ~ resource "aws_instance" "web" {
        id            = "i-0a1b2c3d4e5f6a7b8"
      ~ tags          = {
          ~ "Name" = "tflabs-web" -> "prod-web-DO-NOT-DELETE"
        }
        # (28 unchanged attributes hidden)
    }

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  ~ update in-place

Terraform will perform the following actions:

  # aws_instance.web will be updated in-place
  ~ resource "aws_instance" "web" {
        id            = "i-0a1b2c3d4e5f6a7b8"
      ~ tags          = {
          ~ "Name" = "prod-web-DO-NOT-DELETE" -> "tflabs-web"
        }
        # (28 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy."""

DRIFT = card(
    "12 &middot; Drift",
    "Drift: when reality stops matching the file",
    [
        p(
            "<strong>Drift</strong> is any difference between what your configuration says "
            "and what actually exists, caused by something other than Terraform. Someone "
            "edits a setting in the web console. An automated script changes a tag. A "
            "colleague deletes a resource by hand at 2am to stop an alert. The file did not "
            "change; the world did."
        ),
        h3("Step 1 — the state you applied"),
        p(
            "You wrote this and ran "
            f"{c('terraform apply')}. Terraform created the instance and recorded its ID and "
            "attributes in state."
        ),
        pre(DRIFT_TF),
        h3("Step 2 — someone changes it by hand"),
        p(
            "A colleague opens the AWS console, finds the instance, and edits its "
            f"{c('Name')} tag from {c('tflabs-web')} to {c('prod-web-DO-NOT-DELETE')}. They "
            "do not tell you. Three facts now disagree:"
        ),
        tbl(
            ["Source", "Value of the Name tag"],
            [
                ("Your <code>.tf</code> file", "<code>tflabs-web</code> — unchanged."),
                (
                    "Terraform state",
                    "<code>tflabs-web</code> — still recording what was true at the last "
                    "apply.",
                ),
                (
                    "AWS, right now",
                    "<code>prod-web-DO-NOT-DELETE</code> — the only one of the three that is "
                    "actually true.",
                ),
            ],
            first_col_width="24%",
        ),
        h3("Step 3 — plan detects it by refreshing"),
        p(
            f"Before comparing anything, {c('terraform plan')} <strong>refreshes</strong>: it "
            "asks the provider for the current attributes of every resource in state and "
            "updates its in-memory picture. That is the step that finds drift. The plan then "
            "reports it in two parts — first what changed outside Terraform, then what "
            "Terraform intends to do about it."
        ),
        pre(DRIFT_PLAN, output=True),
        tbl(
            ["Part of the output", "How to read it"],
            [
                (
                    "<code>Refreshing state...</code>",
                    "Terraform asking AWS what is true now. Nothing is changed by this.",
                ),
                (
                    "<code>Objects have changed outside of Terraform</code>",
                    "The drift report. Reading right to left in this block: the tag "
                    "<em>was</em> <code>tflabs-web</code> in state and <em>is now</em> "
                    "<code>prod-web-DO-NOT-DELETE</code> in AWS.",
                ),
                (
                    "<code>will be updated in-place</code>",
                    "The proposed fix, marked with the <code>~</code> symbol from section 10. "
                    "The arrow now points the other way: from what AWS has back to what your "
                    "file says.",
                ),
                (
                    "<code>Plan: 0 to add, 1 to change, 0 to destroy.</code>",
                    "One resource modified, nothing created or deleted. Exactly what a tag "
                    "edit should cost.",
                ),
            ],
            first_col_width="30%",
        ),
        h3("Step 4 — what apply does about it"),
        p(
            f"{c('terraform apply')} sets the tag back to {c('tflabs-web')} and updates "
            "state. The configuration always wins: Terraform's job is to make reality match "
            "the file, so a hand-made change is treated as a mistake to be corrected, not as "
            "a new intention to be adopted. If the colleague's change was actually right, the "
            "fix is to edit the "
            f"{c('.tf')} file and apply that — never to edit the console again."
        ),
        note(
            "Drift is why state alone is not enough, and why it works. State remembers what "
            "Terraform did; refresh discovers what is true; the configuration says what "
            "should be true. The plan is the difference between the last two, expressed as "
            "the change needed to satisfy the third."
        ),
        note(
            "Not all drift is a cheap fix. If someone changes something that cannot be "
            f"altered on a live resource, the plan shows {c('-/+')} replace instead of "
            f"{c('~')}, and applying it destroys the resource and builds a new one. Always "
            "read the symbols before confirming.",
            warn=True,
        ),
        lablink(LAB08, "Lab 08 — local state"),
    ],
)


# --------------------------------------------------------------------------------------
# where to go next
# --------------------------------------------------------------------------------------

NEXT = card(
    "Next",
    "Where to go next",
    [
        p(
            "You now know what Terraform is, what HCL looks like, what a provider is, how to "
            "read a version constraint, what the core commands do, what state is and why "
            "drift matters. That is everything the labs assume. Two steps remain before you "
            "write your first configuration."
        ),
        tbl(
            ["Go here", "Why"],
            [
                (
                    link("./aws-primer.html", "AWS Primer"),
                    "The same treatment for AWS: region, VPC, subnet, internet gateway, route "
                    "table, security group, EC2 instance, key pair and access keys, each with "
                    "its Terraform resource type. Read it next if you have never opened the "
                    "AWS console.",
                ),
                (
                    link(LAB00, "Lab 00 — AWS setup and init"),
                    "Hands on. Check your Terraform version, set up AWS credentials safely, "
                    f"write your first {c('terraform')} and {c('provider')} block, and run "
                    f"{c('terraform init')} successfully. It creates nothing billable.",
                ),
            ],
            first_col_width="34%",
        ),
        h3("Reference for later"),
        tbl(
            ["Lab", "Covers the section"],
            [
                (
                    link(LAB01, "Lab 01 — providers and init"),
                    "Sections 7, 8 and 9 — providers, the registry, and version constraints.",
                ),
                (
                    link(LAB04, "Lab 04 — plan, apply, destroy"),
                    "Sections 1 and 10 — the declarative workflow and the plan symbols, using "
                    "a provider that costs nothing.",
                ),
                (
                    link(LAB05, "Lab 05 — fmt and validate"),
                    f"Section 6 — {c('terraform fmt')} and {c('terraform validate')}.",
                ),
                (
                    link(LAB08, "Lab 08 — local state"),
                    "Sections 11 and 12 — the state file and drift.",
                ),
            ],
            first_col_width="34%",
        ),
    ],
)


# --------------------------------------------------------------------------------------

def build() -> str:
    body = "".join(
        [
            INTRO,
            WHAT_IT_IS,
            WHY,
            OWNERSHIP,
            VERSIONS,
            HCL,
            BASICS,
            PROVIDERS,
            ADD_PROVIDER,
            CONSTRAINTS,
            COMMANDS,
            STATE,
            DRIFT,
            NEXT,
        ]
    )
    return page(
        "Terraform 101",
        "Infrastructure as code from absolute zero — read this before anything else",
        body,
        active="tf101",
        stats=[
            "12 sections",
            f"Targets Terraform {TRACK_TF}",
            f"AWS provider {TRACK_AWS}",
            "No prior knowledge assumed",
        ],
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
