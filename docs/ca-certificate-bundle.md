# `global-bundle.pem`: public CA certificates

## Purpose

[`global-bundle.pem`](../global-bundle.pem) is an Amazon RDS certificate-authority bundle. A database client can use the public CA certificates to verify a database server's TLS certificate. AWS also documents this bundle for Amazon DocumentDB connections.

The bundle does not authenticate you to AWS or log you into a database. It is separate from AWS access keys, database passwords, and private keys. The `.pem` extension describes an encoding format; inspect the contents to determine whether a particular PEM file holds public certificates or private material.

## Inspection on 2026-10-26

The repository copy was inspected without reading `.env` or other credential files:

- It contains 111 PEM certificate blocks, all successfully parsed by OpenSSL.
- Its PEM block type is exclusively `CERTIFICATE`, with Amazon RDS subjects; no private-key blocks were found.
- All 111 certificate SHA-256 fingerprints match certificates in the bundle downloaded over HTTPS from the AWS public trust-store URL below.
- The current AWS download contains 114 distinct certificates, so the local copy is older and lacks three certificates present in that download. The two files are not byte-identical.
- A repository search found no direct reference to `global-bundle.pem` in the searched code and documentation before this note was added. Environment files were deliberately excluded, so this does not prove the file is unused by every local or external configuration.

## Risk assessment

Publishing this verified public CA bundle does not expose private keys or account credentials. Possession of these certificates does not grant access to an AWS account or database.

A CA bundle is still a trust input. Keep its origin verifiable and do not replace it with an untrusted file. An outdated bundle may cause connection failures if a database uses a CA that it does not contain. Having three fewer certificates does not, by itself, establish that an existing connection is broken or compromised.

No certificate file or TLS configuration was changed during this inspection. If the application needs this bundle, refresh it from AWS and test the affected database connection before changing a deployed trust store. Continue to verify the server certificate and hostname; do not disable TLS verification to work around certificate errors.

## Official sources

- [Amazon RDS: TLS and certificate bundles](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html).
- [Amazon DocumentDB: CA certificate updates](https://docs.aws.amazon.com/documentdb/latest/devguide/ca_cert_rotation.html).
- [AWS public trust-store download](https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem).


## Plain-language explanation / 通俗解释

> Saved / 保存日期：2026-10-26。

### 中文：为什么需要这个文件？

**它是数据库连接时用来“验明服务器身份”的证书包，不是你的密码。**

例如，程序连接AWS数据库时：

```text
你的程序 → 连接数据库
               ↓
数据库出示自己的TLS证书
               ↓
程序用global-bundle.pem中的CA证书验证
               ↓
确认证书链可信、服务器主机名等检查通过
               ↓
继续建立受验证的加密连接
```

可以把**CA理解成颁发证件的机构**。这个文件保存的是这些机构的公开验证材料，帮助程序判断：“对方的证书是不是可信机构签发的？”这里的流程图是概念说明，不展开完整TLS握手；客户端也应核对目标主机名和证书有效期。

**“111张公开证书，没有私钥”是什么意思？**

| 内容 | 用途 | 是否需要保密 |
| --- | --- | --- |
| 文件中的CA证书 | 验证服务器证书 | 公开材料，可以分享 |
| 私钥 | 证明身份、参与密码学运算 | 必须保密；这个文件里没有 |
| 数据库用户名／密码 | 登录数据库 | 密码必须保密；也不在这个文件里 |

**别人拿到这个文件，不能因此登录你的数据库或AWS账号。** AWS本身就公开提供它下载。[AWS官方说明](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html)

**项目一定需要它吗？不一定。** 只有数据库客户端被配置为使用它验证连接时才需要。之前检查没有发现代码直接引用它，但没有检查.env，所以目前只能确认它是什么，不能确认当前连接正在使用它。有些客户端使用系统或驱动自带的信任库，不需要单独指定这个文件。

它与Terraform登录、AWS Provider认证是两件事。111张是本仓库检查时的证书数量，不是每个数据库都需要111张，也不是111个用户或111份密钥。

### English: why is this file needed?

**This bundle helps a database client verify the server's identity. It is not your password.**

```text
Your application connects to a database
    → The server presents its TLS certificate
    → The client checks its chain against trusted CA certificates
    → Hostname, validity, and other required checks pass
    → An authenticated encrypted connection can proceed
```

This is a conceptual explanation, not a complete TLS handshake diagram. A certificate authority (CA) issues certificates; the bundle contains public verification material that lets the client check the server's certificate chain.

| Item | Purpose | Confidential? |
| --- | --- | --- |
| Public CA certificates in this bundle | Verify server certificates | No; publicly distributable |
| Private keys | Prove identity and perform cryptographic operations | Yes; none are present in this file |
| Database username/password | Database login | The password must remain secret; neither is included here |

Possessing the bundle does not grant database or AWS account access. AWS publishes it for download.

The project only needs this particular file if a client is configured to use it. The previous code search found no direct reference, but excluded.env files, so actual use has not been established. Some clients use their system or driver trust store instead.

This is separate from Terraform/AWS Provider authentication. The count of 111 describes this inspected copy; it does not mean one database requires 111 certificates or that the file contains 111 users or private keys.
