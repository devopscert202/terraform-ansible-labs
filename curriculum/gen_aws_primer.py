#!/usr/bin/env python3
"""Generate terraform/html/aws-primer.html.

AWS concepts for a learner who has never opened the console, followed by a hand-authored
inline SVG of the lab10 topology. Self-contained: no CDN, no external fonts, no raster
images. Re-running overwrites the output byte-for-byte.

    python3 curriculum/gen_aws_primer.py
"""

from pathlib import Path

from tf_style import esc, page, topic

OUT = Path(__file__).resolve().parent.parent / "terraform" / "html" / "aws-primer.html"

MANUALS = "../labmanuals"

TOPICS = [
    (
        "Where things live",
        "Region and Availability Zone",
        "A <strong>region</strong> is a geographic cluster of AWS data centres, such as "
        "<code class=\"inline\">us-east-2</code> in North Virginia. Every resource you create "
        "belongs to exactly one region, and resources in different regions cannot see each "
        "other by default. An <strong>Availability Zone</strong> (AZ) is one isolated "
        "data-centre group inside a region, named by suffixing a letter: "
        "<code class=\"inline\">us-east-2a</code>. This whole track uses "
        "<code class=\"inline\">us-east-2</code>.",
        'provider "aws" {\n'
        '  region = "us-east-2"\n'
        "}",
        [
            ("<code>provider &quot;aws&quot;</code>",
             "Configures the AWS provider — the plugin that turns your configuration into AWS "
             "API calls. There is no Terraform resource for a region; the region is a provider "
             "setting."),
            ("<code>region</code>",
             "Every resource managed by this provider block is created here. Change it and "
             "Terraform will plan to recreate everything elsewhere."),
            ("Availability Zone",
             "Not set here. It is an argument on zonal resources such as subnets, and this "
             "track never hardcodes one — it is resolved from "
             "<code>data &quot;aws_availability_zones&quot;</code>. The subnet section below "
             "shows how."),
        ],
        f"{MANUALS}/lab00-aws-setup-and-init.md",
        "Lab 00 — AWS setup and init",
    ),
    (
        "Your network",
        "VPC and CIDR",
        "A <strong>VPC</strong> (Virtual Private Cloud) is your own private network inside a "
        "region. Nothing outside it can reach into it unless you explicitly open a path. Its "
        "size is fixed at creation by a <strong>CIDR block</strong> — a range of IP addresses "
        "written as address plus prefix length. <code class=\"inline\">10.0.0.0/16</code> "
        "reserves 65,536 addresses from 10.0.0.0 to 10.0.255.255; the smaller the number after "
        "the slash, the larger the range.",
        'resource "aws_vpc" "this" {\n'
        '  cidr_block           = "10.0.0.0/16"\n'
        "  enable_dns_hostnames = true\n\n"
        '  tags = { Name = "tflabs-capstone", Lab = "lab10" }\n'
        "}",
        [
            ("<code>aws_vpc</code>", "The Terraform resource type for a VPC."),
            ("<code>cidr_block</code>",
             "The address range. It cannot be shrunk later, so pick a /16 and carve subnets "
             "out of it."),
            ("<code>enable_dns_hostnames</code>",
             "Gives instances with a public IP a resolvable public DNS name."),
            ("<code>tags</code>",
             "Free-form key/value labels. Every resource in this track carries "
             "<code>Name</code> and <code>Lab</code>."),
        ],
        f"{MANUALS}/lab02-console-vpc.md",
        "Lab 02 — build a VPC in the console",
        # 8th element: rendered as the card's note. See build().
        "<strong>Check you have a default VPC before your first apply.</strong> An "
        "<code class=\"inline\">aws_instance</code> with no "
        "<code class=\"inline\">subnet_id</code>, or an "
        "<code class=\"inline\">aws_security_group</code> with no "
        "<code class=\"inline\">vpc_id</code>, is placed in the region's <em>default VPC</em> — "
        "a VPC AWS pre-creates per region. A fresh training account may have none, and "
        "<code class=\"inline\">terraform plan</code> does not detect it: the failure appears "
        "only at apply, as "
        "<code class=\"inline\">VPCIdNotSpecified: No default VPC for this user</code>. "
        "Labs 15 and 21 rely on it; every other AWS lab builds its own network. Check, then create one if the result is empty:"
        "<pre>aws ec2 describe-vpcs --filters Name=isDefault,Values=true \\\n"
        "    --query 'Vpcs[].VpcId' --output text\n\n"
        "aws ec2 create-default-vpc</pre>"
        "Lab 10 is unaffected because it builds its own VPC and sets "
        "<code class=\"inline\">subnet_id</code> and <code class=\"inline\">vpc_id</code> "
        "explicitly. That is the better pattern: the network a resource lands in is stated in "
        "the configuration rather than inherited from whatever the account happens to have.",
    ),
    (
        "Slicing the network",
        "Subnet — public versus private",
        "A <strong>subnet</strong> is a slice of the VPC's address range, pinned to one "
        "Availability Zone. The words public and private are not AWS settings: a subnet is "
        "<em>public</em> when its route table sends internet-bound traffic to an internet "
        "gateway, and <em>private</em> when it does not. "
        "<code class=\"inline\">map_public_ip_on_launch</code> additionally hands every "
        "instance launched there a public IP address.",
        'data "aws_availability_zones" "available" {\n'
        '  state = "available"\n'
        "}\n\n"
        'resource "aws_subnet" "public" {\n'
        "  vpc_id                  = aws_vpc.this.id\n"
        '  cidr_block              = "10.0.1.0/24"\n'
        "  availability_zone       = data.aws_availability_zones.available.names[0]\n"
        "  map_public_ip_on_launch = true\n"
        "}",
        [
            ("<code>aws_subnet</code>", "The Terraform resource type for a subnet."),
            ("<code>vpc_id</code>",
             "Places the subnet inside the VPC. This reference is also what tells Terraform to "
             "create the VPC first."),
            ("<code>cidr_block</code>",
             "A /24 (256 addresses) carved out of the VPC's /16. Subnet ranges may not overlap."),
            ("<code>data &quot;aws_availability_zones&quot;</code>",
             "Asks the account which zones it can actually use. Zone names are mapped per "
             "account, so <code>us-east-2a</code> is not the same hardware in two accounts and "
             "may be absent or out of capacity in yours."),
            ("<code>availability_zone</code>",
             "Pins the subnet to one AZ, which must sit inside the provider's region. Take it "
             "from the data source with <code>names[0]</code> rather than hardcoding a name — "
             "this is what Lab 10 does, and it is not a value you set by hand."),
            ("<code>map_public_ip_on_launch</code>",
             "Auto-assigns a public IPv4 address to instances launched in this subnet."),
        ],
        f"{MANUALS}/lab02-console-vpc.md",
        "Lab 02 — build a VPC in the console",
    ),
    (
        "The way out",
        "Internet Gateway",
        "An <strong>internet gateway</strong> is the door between your VPC and the public "
        "internet. It is a single, horizontally scaled component you attach to one VPC — you "
        "do not size it, patch it, or pay for it. Creating one changes nothing on its own: "
        "traffic only uses it once a route table points at it.",
        'resource "aws_internet_gateway" "this" {\n'
        "  vpc_id = aws_vpc.this.id\n\n"
        '  tags = { Name = "tflabs-capstone-igw", Lab = "lab10" }\n'
        "}",
        [
            ("<code>aws_internet_gateway</code>",
             "The Terraform resource type. One per VPC is the normal case."),
            ("<code>vpc_id</code>",
             "Attaches the gateway to the VPC. An unattached gateway carries no traffic."),
        ],
        f"{MANUALS}/lab10-capstone-vpc-ec2.md",
        "Lab 10 — the capstone build",
    ),
    (
        "Traffic direction",
        "Route table",
        "A <strong>route table</strong> is a list of rules that answer one question: for a "
        "given destination address, where do I send the packet? Each rule pairs a destination "
        "CIDR with a target. Every VPC has a default local route so subnets can talk to each "
        "other; you add <code class=\"inline\">0.0.0.0/0</code> pointing at the internet "
        "gateway to reach everything else. A table only affects a subnet once it is "
        "<em>associated</em> with it.",
        'resource "aws_route_table" "public" {\n'
        "  vpc_id = aws_vpc.this.id\n\n"
        "  route {\n"
        '    cidr_block = "0.0.0.0/0"\n'
        "    gateway_id = aws_internet_gateway.this.id\n"
        "  }\n"
        "}\n\n"
        'resource "aws_route_table_association" "public" {\n'
        "  subnet_id      = aws_subnet.public.id\n"
        "  route_table_id = aws_route_table.public.id\n"
        "}",
        [
            ("<code>aws_route_table</code>", "The Terraform resource type for the table itself."),
            ("<code>route</code>",
             "One rule. <code>0.0.0.0/0</code> means every address not matched by a more "
             "specific route — the default route."),
            ("<code>gateway_id</code>", "Sends that traffic to the internet gateway."),
            ("<code>aws_route_table_association</code>",
             "Binds the table to a subnet. Without it the subnet keeps the VPC's main table "
             "and stays private."),
        ],
        f"{MANUALS}/lab10-capstone-vpc-ec2.md",
        "Lab 10 — the capstone build",
    ),
    (
        "Instance firewall",
        "Security group",
        "A <strong>security group</strong> is a stateful firewall attached to an instance's "
        "network interface. <em>Ingress</em> rules allow traffic in, <em>egress</em> rules "
        "allow it out, and everything not explicitly allowed is denied. Stateful means a reply "
        "to an allowed inbound request is automatically allowed back out, so you rarely need "
        "matching rule pairs.",
        'resource "aws_security_group" "web" {\n'
        '  description = "Allow inbound web traffic, all outbound"\n'
        "  vpc_id      = aws_vpc.this.id\n\n"
        '  dynamic "ingress" {\n'
        "    for_each = var.ingress_ports  # [80]\n"
        "    content {\n"
        "      from_port   = ingress.value\n"
        "      to_port     = ingress.value\n"
        '      protocol    = "tcp"\n'
        "      cidr_blocks = [var.allowed_cidr]\n"
        "    }\n"
        "  }\n\n"
        "  egress {\n"
        "    from_port   = 0\n"
        "    to_port     = 0\n"
        '    protocol    = "-1"\n'
        '    cidr_blocks = ["0.0.0.0/0"]\n'
        "  }\n"
        "}",
        [
            ("<code>aws_security_group</code>", "The Terraform resource type."),
            ("<code>vpc_id</code>",
             "Places the group in your VPC. Omit it and the group is created in the region's "
             "default VPC instead — see the warning in the VPC section above."),
            ("<code>dynamic &quot;ingress&quot;</code>",
             "Generates one ingress rule per element of the list instead of repeating the "
             "block by hand. Lab 10 opens a single port, 80."),
            ("<code>from_port</code> / <code>to_port</code>",
             "A port range. Setting both to the same number opens exactly one port."),
            ("<code>cidr_blocks</code>",
             "Who may connect. Lab 10's <code>allowed_cidr</code> defaults to "
             "<code>0.0.0.0/0</code>, the entire internet — defensible for a public web port, "
             "dangerous for an administrative port such as SSH on 22. Narrow it to your own "
             "address outside a lab account."),
            ("<code>egress</code>",
             "Outbound, written as one ordinary block. Groups are stateful, so replies to "
             "allowed inbound requests need no rule of their own."),
        ],
        f"{MANUALS}/lab10-capstone-vpc-ec2.md",
        "Lab 10 — the capstone build",
    ),
    (
        "Compute",
        "EC2 instance",
        "An <strong>EC2 instance</strong> is a virtual machine. You choose an "
        "<strong>instance type</strong> for its CPU and memory (<code "
        "class=\"inline\">t3.micro</code> here) and an <strong>AMI</strong> — a machine image "
        "that supplies the operating system. Resolve the AMI with a data source rather than "
        "pasting an ID, because IDs differ per region and change whenever AWS republishes the "
        "image. <code class=\"inline\">user_data</code> is a script run once on first boot.",
        'data "aws_ami" "al2023" {\n'
        "  most_recent = true\n"
        '  owners      = ["amazon"]\n\n'
        "  filter {\n"
        '    name   = "name"\n'
        '    values = ["al2023-ami-2023.*-x86_64"]\n'
        "  }\n"
        "}\n\n"
        'resource "aws_instance" "web" {\n'
        "  ami           = data.aws_ami.al2023.id\n"
        '  instance_type = "t3.micro"\n'
        "  subnet_id     = aws_subnet.public.id\n"
        "}",
        [
            ("<code>data &quot;aws_ami&quot;</code>",
             "Reads an existing image rather than creating one. Data sources look things up; "
             "resources create things."),
            ("<code>most_recent</code>",
             "Of the images matching the filters, take the newest. Combined with the name "
             "filter this always yields current Amazon Linux 2023."),
            ("<code>aws_instance</code>", "The Terraform resource type for a virtual machine."),
            ("<code>subnet_id</code>",
             "Places the instance in the public subnet, which is what earns it a public IP."),
        ],
        f"{MANUALS}/lab03-first-ec2.md",
        "Lab 03 — your first EC2 instance",
    ),
    (
        "Instance login",
        "Key pair",
        "A <strong>key pair</strong> is an SSH public/private key used to log into a Linux "
        "instance. AWS stores the public half and attaches it to the instance at launch; the "
        "private half stays on your machine and is never uploaded. No lab in this track creates "
        "a key pair: the capstone is verified over HTTP, and Lab 15 connects over SSH to a host "
        "you supply, reading an existing private key from disk.",
        'resource "aws_key_pair" "lab" {\n'
        '  key_name   = "tflabs-key"\n'
        '  public_key = file("~/.ssh/id_rsa.pub")\n'
        "}\n\n"
        'resource "aws_instance" "web" {\n'
        "  key_name = aws_key_pair.lab.key_name\n"
        "  # ...\n"
        "}",
        [
            ("<code>aws_key_pair</code>", "The Terraform resource type."),
            ("<code>public_key</code>",
             "Only the public half. Never place a private key in a <code>.tf</code> file or in "
             "git."),
            ("<code>key_name</code>",
             "On the instance, names the key injected at launch. It cannot be changed without "
             "replacing the instance."),
            ("using an existing key",
             "Lab 15 skips <code>aws_key_pair</code> entirely and reads a private key you "
             "already have with "
             "<code>private_key = file(pathexpand(var.private_key_path))</code>, marked "
             "<code>sensitive = true</code>."),
        ],
        f"{MANUALS}/lab15-remote-exec-provisioner.md",
        "Lab 15 — remote-exec provisioner",
    ),
    (
        "Authentication",
        "IAM access keys",
        "Terraform calls the AWS API as some identity, and in a lab account that identity is "
        "an IAM user holding an <strong>access key</strong>. The pair is an access key ID "
        "(begins <code class=\"inline\">AKIA</code>, not secret) and a secret access key "
        "(shown exactly once, fully secret). Supply them as environment variables, never as "
        "arguments in a <code class=\"inline\">.tf</code> file, and rotate them when the lab "
        "ends.",
        'unset AWS_PROFILE AWS_SESSION_TOKEN\n'
        'export AWS_ACCESS_KEY_ID="AKIA..."\n'
        'export AWS_SECRET_ACCESS_KEY="..."\n'
        'export AWS_DEFAULT_REGION="us-east-2"\n\n'
        "aws sts get-caller-identity",
        [
            ("<code>unset AWS_PROFILE</code>",
             "A leftover profile overrides these variables. Set to an empty string it fails "
             "with <code>The config profile () could not be found</code>."),
            ("<code>AWS_ACCESS_KEY_ID</code>",
             "Identifies the IAM user. The AWS provider reads it automatically — no "
             "credentials argument is required."),
            ("<code>AWS_SECRET_ACCESS_KEY</code>",
             "The secret half. Treat it like a password: no <code>.tf</code> file, no git, no "
             "screenshot."),
            ("<code>aws sts get-caller-identity</code>",
             "Confirms which account and identity Terraform will act as. Run it before every "
             "apply."),
        ],
        f"{MANUALS}/lab00-aws-setup-and-init.md",
        "Lab 00 — AWS setup and init",
    ),
]


def box(x, y, w, h, stroke, fill, *, dash="", rx=10):
    """One rectangle of the topology diagram."""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"{d} />')


def label(x, y, text, *, size=13, color="#0f172a", weight="700", anchor="start", mono=False):
    """One <text> label. No embedded fonts: system stacks only."""
    family = ("&quot;SF Mono&quot;, Menlo, Consolas, monospace" if mono
              else "&quot;Segoe UI&quot;, system-ui, sans-serif")
    return (f'    <text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{text}</text>')


def arrow(d, *, color="#2563eb", width="2.2", marker="arrowhead", dash=""):
    """Traffic arrow. `dash` turns it into a configuration relationship, not a packet path."""
    s = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'    <path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{s} '
            f'marker-end="url(#{marker})" />')


BLUE, CYAN, SLATE, SLATE_MID, GREEN = "#2563eb", "#06b6d4", "#0f172a", "#64748b", "#16a34a"


def diagram() -> str:
    """Hand-authored inline SVG of exactly what lab10 builds."""
    parts = [
        '<svg viewBox="0 0 1060 700" role="img" '
        'aria-label="Lab 10 topology. A request from the internet enters the AWS region through '
        'the internet gateway, passes into the public subnet, is admitted by the security group '
        'on TCP port 80, and reaches the EC2 instance running httpd, which replies back out '
        'through the gateway. The route table is shown with dashed lines because it configures '
        'the path rather than carrying traffic: its 0.0.0.0/0 route targets the internet '
        'gateway, and it is associated with the public subnet.">',
        "    <defs>",
        '        <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '            <path d="M 0 0 L 10 5 L 0 10 z" fill="#2563eb" />',
        "        </marker>",
        '        <marker id="arrowhead-green" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '            <path d="M 0 0 L 10 5 L 0 10 z" fill="#16a34a" />',
        "        </marker>",
        '        <marker id="arrowhead-grey" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />',
        "        </marker>",
        "    </defs>",
        '    <rect x="0" y="0" width="1060" height="700" fill="#f8fafc" />',

        # --- outside the region -------------------------------------------------
        box(20, 190, 160, 84, SLATE_MID, "#ffffff"),
        label(100, 222, "Internet", size=15, anchor="middle"),
        label(100, 244, "browser / curl", size=11, color=SLATE_MID, weight="600",
              anchor="middle"),

        box(20, 470, 160, 84, GREEN, "#f0fdf4"),
        label(100, 500, "http://&lt;public_ip&gt;", size=12, color="#166534", anchor="middle",
              mono=True),
        label(100, 522, "output web_url", size=11, color=SLATE_MID, weight="600",
              anchor="middle"),

        # --- region -------------------------------------------------------------
        box(220, 30, 810, 640, SLATE_MID, "#ffffff", dash="7 5", rx=14),
        label(240, 58, "AWS Region", size=15, color=SLATE),
        label(340, 58, "us-east-2", size=13, color=SLATE_MID, weight="600", mono=True),
        label(1010, 58, "provider aws { region }", size=11, color=SLATE_MID, weight="600",
              anchor="end", mono=True),

        # --- vpc ----------------------------------------------------------------
        box(250, 80, 750, 570, BLUE, "#f8fbff", rx=14),
        label(272, 108, "VPC 10.0.0.0/16", size=15, color=BLUE),
        label(978, 108, "aws_vpc", size=12, color=BLUE, anchor="end", mono=True),

        # --- igw ----------------------------------------------------------------
        box(280, 140, 240, 78, CYAN, "#ecfeff"),
        label(400, 170, "Internet Gateway", size=13, color="#0e7490", anchor="middle"),
        label(400, 194, "aws_internet_gateway", size=11, color=SLATE_MID, weight="600",
              anchor="middle", mono=True),

        # --- route table --------------------------------------------------------
        box(610, 140, 300, 78, CYAN, "#ecfeff"),
        label(760, 166, "Route Table 0.0.0.0/0 &#8594; IGW", size=13, color="#0e7490",
              anchor="middle"),
        label(760, 190, "aws_route_table", size=11, color=SLATE_MID, weight="600",
              anchor="middle", mono=True),
        label(760, 208, "+ aws_route_table_association", size=10, color=SLATE_MID,
              weight="600", anchor="middle", mono=True),

        # --- public subnet ------------------------------------------------------
        box(280, 290, 630, 330, BLUE, "#eff6ff", rx=12),
        label(302, 318, "Public Subnet 10.0.1.0/24", size=14, color="#1d4ed8"),
        label(888, 318, "aws_subnet", size=12, color="#1d4ed8", anchor="end", mono=True),
        label(302, 338, "map_public_ip_on_launch = true", size=10, color=SLATE_MID,
              weight="600", mono=True),

        # --- security group -----------------------------------------------------
        box(320, 360, 550, 230, CYAN, "#ffffff", rx=12),
        label(342, 388, "Security Group", size=13, color="#0e7490"),
        label(848, 388, "aws_security_group", size=11, color="#0e7490", anchor="end",
              mono=True),
        label(342, 408, "ingress tcp 80 &#183; egress all", size=11,
              color=SLATE_MID, weight="600", mono=True),

        # --- ec2 ----------------------------------------------------------------
        box(360, 430, 470, 140, BLUE, "#dbeafe", rx=12),
        label(595, 462, "EC2 instance &#183; t3.micro", size=14, color="#1d4ed8",
              anchor="middle"),
        label(595, 484, "aws_instance", size=11, color=SLATE_MID, weight="600",
              anchor="middle", mono=True),
        label(595, 508, "Amazon Linux 2023 via data aws_ami", size=11, color=SLATE_MID,
              weight="600", anchor="middle", mono=True),
        label(595, 530, "user_data: dnf install httpd &#183; systemctl enable --now httpd",
              size=10, color=SLATE_MID, weight="600", anchor="middle", mono=True),
        label(595, 554, "public IPv4 &#183; port 80 open", size=11, color=GREEN,
              anchor="middle"),

        # --- request path (solid blue: packets actually traverse these) ----------
        # 1 internet -> internet gateway
        arrow("M 180 224 L 250 224 L 250 179 L 274 179"),
        label(206, 216, "1", size=11, color=BLUE, anchor="middle"),

        # 2 internet gateway -> public subnet. Traffic goes straight from the IGW into the
        # subnet; it does not travel "through" the route table, which is why the old
        # IGW -> route table arrow was wrong.
        arrow("M 400 218 L 400 284"),
        label(412, 256, "2", size=11, color=BLUE),

        # 3 subnet -> security group
        arrow("M 595 344 L 595 354"),
        label(607, 352, "3", size=11, color=BLUE),

        # 4 security group ingress tcp 80 -> EC2
        arrow("M 595 414 L 595 424"),
        label(607, 422, "4", size=11, color=BLUE),

        # 5 reply
        arrow("M 360 500 L 250 500 L 250 512 L 186 512", color=GREEN,
              marker="arrowhead-green"),
        label(300, 492, "5 reply", size=11, color=GREEN, anchor="middle"),

        # --- configuration relationships (dashed grey: not a traffic hop) -------
        # The route table makes step 2 possible: its default route targets the IGW and the
        # table is associated with the public subnet.
        arrow("M 604 179 L 526 179", color=SLATE_MID, width="1.8", marker="arrowhead-grey",
              dash="5 4"),
        label(563, 170, "route target", size=10, color=SLATE_MID, weight="600",
              anchor="middle"),

        arrow("M 760 218 L 760 284", color=SLATE_MID, width="1.8", marker="arrowhead-grey",
              dash="5 4"),
        label(772, 256, "associated with subnet", size=10, color=SLATE_MID, weight="600"),

        # --- legend -------------------------------------------------------------
        label(240, 682,
              "Solid blue 1&#8211;5: the path a request takes. "
              "Dashed grey: route table configuration, which permits the path but carries "
              "no traffic itself.",
              size=11, color=SLATE_MID, weight="600"),
        "</svg>",
    ]
    return "\n".join(parts)


def build() -> str:
    cards = []
    for entry in TOPICS:
        eyebrow, heading, concept, code, rows, href, lab_label = entry[:7]
        note = entry[7] if len(entry) > 7 else ""
        cards.append(
            topic(eyebrow, heading, concept, esc(code), rows, href, lab_label, lang_note=note)
        )

    intro = """        <div class="card">
            <span class="eyebrow">Start here</span>
            <h2>AWS in nine ideas</h2>
            <p class="concept">This page assumes you have never opened the AWS console. Each
            section below defines one AWS concept in plain English and names the Terraform
            resource type that creates it, in the order the pieces stack up: a region holds a
            VPC, the VPC holds subnets, a subnet holds an instance, and a gateway plus a route
            table make that instance reachable. The diagram at the end is exactly what
            <a class="lablink" href="%s/lab10-capstone-vpc-ec2.md"
               style="margin:0;">Lab 10</a> builds.</p>
            <div class="note"><strong>Read <a href="./terraform-101.html">Terraform 101</a>
            first.</strong> This page teaches AWS, not Terraform. It shows HCL &mdash; the
            language Terraform configuration is written in &mdash; to name the resource type
            behind each AWS concept, and it assumes you have already met blocks, arguments and
            references there.</div>
            <h3>How to read the code blocks on this page</h3>
            <p class="concept">Enough to follow along, no more. Terraform 101 covers all of it
            properly.</p>
            <table>
                <thead><tr><th style="width:30%%;">You will see</th><th>What it means</th></tr></thead>
                <tbody>
                    <tr><td class="lineref">resource "aws_vpc" "this" {</td>
                        <td>Create and own one thing. <code class="inline">aws_vpc</code> is the
                        <em>resource type</em> (which kind of AWS object); <code class="inline">this</code>
                        is a name you choose to refer to it elsewhere in your own files.</td></tr>
                    <tr><td class="lineref">data "aws_ami" "al2023" {</td>
                        <td>Only look something up that already exists. It creates nothing.</td></tr>
                    <tr><td class="lineref">cidr_block = "10.0.0.0/16"</td>
                        <td>An <em>argument</em>: a setting inside the block, written as
                        name, equals sign, value.</td></tr>
                    <tr><td class="lineref">vpc_id = aws_vpc.this.id</td>
                        <td>A <em>reference</em> to another block's attribute. It also tells
                        Terraform to create the VPC before this resource.</td></tr>
                    <tr><td class="lineref"># ...</td>
                        <td>A comment. Here it marks arguments omitted for brevity.</td></tr>
                </tbody>
            </table>
        </div>
""" % MANUALS

    diagram_card = f"""        <div class="card">
            <span class="eyebrow">Putting it together</span>
            <h2>The Lab 10 architecture</h2>
            <p class="concept">Seven resources, one reachable web server. Follow the numbered
            blue arrows:
            <strong>1</strong> a request from the internet reaches the internet gateway;
            <strong>2</strong> the gateway passes it into the public subnet;
            <strong>3</strong> it arrives at the security group guarding the instance;
            <strong>4</strong> the ingress rule for TCP 80 admits it to the EC2 instance, where
            <code class="inline">httpd</code> serves the page the user-data script wrote at
            first boot;
            <strong>5</strong> the reply returns the same way. The security group is stateful,
            so the response needs no matching egress rule.</p>
            <p class="concept">The route table is drawn with dashed grey lines because it
            carries no packets. It is what makes step 2 possible: its
            <code class="inline">0.0.0.0/0</code> route targets the internet gateway, and
            <code class="inline">aws_route_table_association</code> binds the table to the
            public subnet. Without the association the subnet falls back to the VPC's main
            table, which has no default route, and step 2 fails. Remove any one piece and the
            path breaks.</p>
            <div class="diagram">
{diagram()}
            </div>
            <table>
                <thead><tr><th style="width:30%;">AWS name</th><th>Terraform resource type</th></tr></thead>
                <tbody>
                    <tr><td class="lineref">VPC</td><td><code class="inline">aws_vpc</code></td></tr>
                    <tr><td class="lineref">Internet gateway</td><td><code class="inline">aws_internet_gateway</code></td></tr>
                    <tr><td class="lineref">Public subnet</td><td><code class="inline">aws_subnet</code></td></tr>
                    <tr><td class="lineref">Route table</td><td><code class="inline">aws_route_table</code> + <code class="inline">aws_route_table_association</code></td></tr>
                    <tr><td class="lineref">Security group</td><td><code class="inline">aws_security_group</code></td></tr>
                    <tr><td class="lineref">EC2 instance</td><td><code class="inline">aws_instance</code></td></tr>
                    <tr><td class="lineref">Machine image</td><td><code class="inline">data.aws_ami</code></td></tr>
                    <tr><td class="lineref">Availability Zone</td><td><code class="inline">data.aws_availability_zones</code> &mdash; the capstone takes the first zone the account can actually use rather than hardcoding <code class="inline">us-east-2a</code></td></tr>
                </tbody>
            </table>
            <div class="warn">The EC2 instance is the only billable resource in the diagram.
            Run <code class="inline">terraform destroy</code> when the lab ends.</div>
            <a class="lablink" href="{MANUALS}/lab10-capstone-vpc-ec2.md">Build it in Lab 10 &rarr;</a>
        </div>
"""

    return page(
        "AWS Primer",
        "Regions, VPCs, subnets, gateways and instances — for a first-time AWS user",
        intro + "".join(cards) + diagram_card,
        active="primer",
        stats=["9 concepts", "Terraform resource types", "Lab 10 architecture diagram"],
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
