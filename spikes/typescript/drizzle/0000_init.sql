CREATE TABLE `action_meter` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`provider` text NOT NULL,
	`model_id` text NOT NULL,
	`tier` text NOT NULL,
	`purpose` text NOT NULL,
	`prompt_version` text NOT NULL,
	`input_tokens` integer NOT NULL,
	`output_tokens` integer NOT NULL,
	`cost_micros` integer NOT NULL,
	`latency_ms` integer NOT NULL,
	`outcome` text NOT NULL,
	`at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `audit_log` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`entity` text NOT NULL,
	`entity_id` text NOT NULL,
	`action` text NOT NULL,
	`actor` text NOT NULL,
	`metadata` text NOT NULL,
	`at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `confirmations` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`draft_id` text NOT NULL,
	`member_id` text NOT NULL,
	`created_at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `confirmations_key` ON `confirmations` (`workspace_id`,`draft_id`,`member_id`);--> statement-breakpoint
CREATE TABLE `drafts` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`source_message_id` text NOT NULL,
	`title` text NOT NULL,
	`outcome` text NOT NULL,
	`proposed_owner_id` text,
	`due_date` text,
	`source_permalink` text NOT NULL,
	`status` text NOT NULL,
	`prompt_version` text NOT NULL,
	`confidence` integer NOT NULL,
	`tracker_task_id` text,
	`created_at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `drafts_source_prompt_key` ON `drafts` (`workspace_id`,`source_message_id`,`prompt_version`);--> statement-breakpoint
CREATE TABLE `jobs` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`queue` text NOT NULL,
	`type` text NOT NULL,
	`payload` text NOT NULL,
	`status` text NOT NULL,
	`attempts` integer DEFAULT 0 NOT NULL,
	`max_attempts` integer DEFAULT 3 NOT NULL,
	`run_at` integer NOT NULL,
	`last_error` text,
	`created_at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `members` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`name` text NOT NULL,
	`role` text NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `source_messages` (
	`workspace_id` text NOT NULL,
	`id` text NOT NULL,
	`channel_id` text NOT NULL,
	`slack_ts` text NOT NULL,
	`author_id` text NOT NULL,
	`text` text NOT NULL,
	`permalink` text NOT NULL,
	`received_at` integer NOT NULL,
	PRIMARY KEY(`workspace_id`, `id`),
	FOREIGN KEY (`workspace_id`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `source_messages_ingest_key` ON `source_messages` (`workspace_id`,`channel_id`,`slack_ts`);--> statement-breakpoint
CREATE TABLE `workspaces` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`budget_micros` integer DEFAULT 1000000 NOT NULL,
	`created_at` integer NOT NULL
);
