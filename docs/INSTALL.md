# Installation & Mobile Guide / 安装及手机使用

## Why I can't see the generated Skill in my ChatGPT plugins

A file created in a ChatGPT conversation is only a generated file. Downloading an `.skill` or `.zip` does **not** install it into your ChatGPT account, GitHub repository, plugin list, or phone. GitHub source hosting and ChatGPT installation are two separate actions.

## Option A — ChatGPT Skills (if eligible)

1. Open ChatGPT and navigate to **Plugins → Skills**.
2. Select **Create** → **Upload from your computer**, or **Create with editor** if offered.
3. Upload a supported skill package, or use `SKILL.md` and its `references/` files in the editor.
4. Follow the scan, review, and install flow; only after successful installation should it appear in **Installed** or **Created by me**.
5. On your phone, sign in with the same ChatGPT account and check **Plugins → Skills / Installed**, if the feature is available on that surface.

Skills are **not** available to all accounts. The current official eligibility document lists select Business, Enterprise, Healthcare and Edu users; actual availability is subject to rollout and workspace controls. See [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).

## Option B — ChatGPT personal Plugin containing the Skill

A skill-only Plugin is a different packaging option and can be created with the **Plugin Creator** capability. It uses a plugin manifest (`plugin.json`) at the archive root and `skills/rolling-fitness-coach/SKILL.md` inside. If Plugin Creator returns a plugin link, open the link from the same ChatGPT account, then check **Plugins → Personal / Installed**. The Plugin may install automatically; availability of its skills or interactive parts can still vary by plan, workspace, and device.

Reference: [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt) and [Package your plugin](https://developers.openai.com/plugins/build/plugins).

## Option C — Compatible Agent Skills tools

Install the folder containing `SKILL.md`, `references/`, `assets/`, and optional scripts into your host's configured skills directory. A GitHub repository can distribute these files but does not automatically install them.

## Mobile behavior and data persistence

- A simple instruction-only Skill/Plugin can work in mobile ChatGPT **when your account and mobile client provide it**; check product settings if it is not visible.
- Do not assume that an optional Python script inside the archive runs on the phone. A mobile chat interface can apply instructions, but persistent local JSON logging must be hosted separately or provided by supported tools.
- Skill installation alone does not guarantee training logs persist across chats. Use the same conversation or explicitly connect an authorized storage solution. Never claim background tracking or notifications are active unless the host confirms them.
- Images and video links depend on access to image and internet tools, and do not come bundled with this repository.

## 常见问题

**Q：为什么手机里没出现？**
A：创建文件和在 ChatGPT 账户中安装是两回事。请检查是否已创建为私人 Plugin / 是否完成 Skill 安装，以及手机登录账户是否一致。

**Q：GitHub 上已经有 README 了，为什么还不能 @调用？**
A：GitHub 仅托管代码。@调用需要在 ChatGPT 中完成相应插件安装或创建，并且客户端提供该入口。

**Q：是否会自动记住我每次健身的数据？**
A：不会默认跨会话永久保存。日志 CLI 可离线保存到用户自己的 JSON 文件；其它持久化方案需要额外配置与用户授权。

**Q：可以在手机上动态汇报训练和饮食吗？**
A：可以在普通聊天中持续汇报。若账户支持该 Skill/Plugin，模型可以按本工作流处理；未安装也可以继续在同一已有对话中使用原本的教练流程。
