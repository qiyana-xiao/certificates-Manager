-- 证件管家 建表脚本（MySQL 8.x）
-- 由 scripts/init_db.py 执行；与 backend/app/models.py 保持一致（以 models 为最终口径）

-- 说明：本脚本只在库/表不存在时创建，绝不删除已有表或数据，
-- 保证「每次启动重复执行」也安全（幂等），用户档案/证件/提醒不会被重建清空。
-- 如需彻底重置（清空全部数据并重建空表），请用：python scripts/init_db.py --reset，慎用。
CREATE DATABASE IF NOT EXISTS `doc_keeper` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `doc_keeper`;

-- 省份参照表：jtw_code 为交管12123平台省份子域名字母码（全部经官网核实）
-- portal_url 仅收录本次已核实的省级政务服务网入口；为空的省份前端回退到国家政务服务平台
CREATE TABLE IF NOT EXISTS `provinces` (
  `code` VARCHAR(8) NOT NULL COMMENT '省份代码，如 GD',
  `name` VARCHAR(20) NOT NULL COMMENT '省份名称',
  `jtw_code` VARCHAR(8) NOT NULL DEFAULT '' COMMENT '交管平台字母码，如 gd',
  `portal_name` VARCHAR(60) NOT NULL DEFAULT '' COMMENT '省级政务平台名称',
  `portal_url` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '省级政务平台入口（未核实的留空）',
  `region_type` VARCHAR(20) NOT NULL DEFAULT '省' COMMENT '直辖市/省/自治区/特别行政区',
  `sort` INT NOT NULL DEFAULT 0,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `password_hash` VARCHAR(300) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `province_code` VARCHAR(8) NULL COMMENT '用户所在省份，用于指南与官方入口按省直达',
  `default_timezone` VARCHAR(50) NOT NULL DEFAULT 'Asia/Shanghai',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `document_types` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(40) NOT NULL,
  `name` VARCHAR(60) NOT NULL,
  `issuer` VARCHAR(100) NOT NULL DEFAULT '',
  `icon` VARCHAR(20) NOT NULL DEFAULT '🪪',
  `default_ahead_days` JSON,
  `valid_years` INT NULL,
  `desc` VARCHAR(300) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_document_types_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `renewal_guides` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `document_type_id` INT NOT NULL,
  `title` VARCHAR(120) NOT NULL,
  `region_code` VARCHAR(8) NULL COMMENT '适用省份代码；NULL=全国通用',
  `link_mode` VARCHAR(20) NOT NULL DEFAULT 'FIXED' COMMENT 'FIXED=固定链接 / PROVINCE_PORTAL=跳转本省政务服务网 / PROVINCE_JTW=跳转本省交管12123',
  `materials` JSON,
  `location` TEXT NULL,
  `fee` VARCHAR(300) NOT NULL DEFAULT '',
  `duration` VARCHAR(200) NOT NULL DEFAULT '',
  `official_url` TEXT NULL,
  `source` VARCHAR(200) NOT NULL DEFAULT '',
  `updated_at` DATE NOT NULL,
  `disclaimer` VARCHAR(200) NOT NULL DEFAULT '以当地窗口实际要求为准，办理前请核实最新政策。',
  PRIMARY KEY (`id`),
  KEY `idx_renewal_guides_type` (`document_type_id`),
  KEY `idx_renewal_guides_region` (`region_code`),
  CONSTRAINT `fk_guides_type` FOREIGN KEY (`document_type_id`) REFERENCES `document_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `family_members` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `host_user_id` INT NOT NULL,
  `member_name` VARCHAR(40) NOT NULL,
  `member_color` VARCHAR(20) NOT NULL DEFAULT '#3b82f6',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_family_host` (`host_user_id`),
  CONSTRAINT `fk_family_user` FOREIGN KEY (`host_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `my_documents` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `document_type_id` INT NULL,
  `member_id` INT NULL,
  `title` VARCHAR(80) NOT NULL,
  `doc_number_cipher` VARCHAR(500) NOT NULL DEFAULT '',
  `start_date` DATE NULL,
  `valid_years` INT NULL,
  `expire_date` DATE NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'VALID',
  `note` VARCHAR(300) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_docs_user` (`user_id`),
  KEY `idx_docs_expire` (`expire_date`),
  CONSTRAINT `fk_docs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_docs_type` FOREIGN KEY (`document_type_id`) REFERENCES `document_types` (`id`),
  CONSTRAINT `fk_docs_member` FOREIGN KEY (`member_id`) REFERENCES `family_members` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `reminder_rules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `document_id` INT NOT NULL,
  `ahead_days` INT NOT NULL,
  `enabled` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rule` (`document_id`, `ahead_days`),
  CONSTRAINT `fk_rules_doc` FOREIGN KEY (`document_id`) REFERENCES `my_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `reminder_jobs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `document_id` INT NOT NULL,
  `rule_id` INT NOT NULL,
  `remind_on` DATE NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_job` (`document_id`, `rule_id`, `remind_on`),
  KEY `idx_jobs_doc` (`document_id`),
  CONSTRAINT `fk_jobs_doc` FOREIGN KEY (`document_id`) REFERENCES `my_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `app_notifications` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `job_id` INT NOT NULL,
  `document_id` INT NOT NULL,
  `document_title` VARCHAR(80) NOT NULL DEFAULT '',
  `content` TEXT NULL,
  `notify_date` DATE NOT NULL COMMENT '弹窗所属日期（同一天同一提醒只弹一次）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING=待弹窗 / DISMISSED=当天已忽略 / DONE=已处理',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_notify_job_date` (`job_id`, `notify_date`),
  KEY `idx_notify_user` (`user_id`),
  KEY `idx_notify_doc` (`document_id`),
  CONSTRAINT `fk_notify_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_notify_job` FOREIGN KEY (`job_id`) REFERENCES `reminder_jobs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notify_doc` FOREIGN KEY (`document_id`) REFERENCES `my_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `export_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `scope` VARCHAR(40) NOT NULL DEFAULT 'all',
  `file_hash` VARCHAR(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `idx_export_user` (`user_id`),
  CONSTRAINT `fk_export_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `admin_id` INT NOT NULL,
  `action` VARCHAR(60) NOT NULL,
  `target` VARCHAR(120) NOT NULL DEFAULT '',
  `detail` TEXT NULL,
  `time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_audit_admin` (`admin_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `system_configs` (
  `key` VARCHAR(60) NOT NULL,
  `value` VARCHAR(300) NOT NULL DEFAULT '',
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;