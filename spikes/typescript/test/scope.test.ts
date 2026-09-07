import assert from 'node:assert/strict';
import { test } from 'node:test';
import { openDb } from '../src/db/client.ts';
import { createWorkspace } from '../src/db/system.ts';

test('workspace scope keeps draft nullable fields explicit and tenant-scoped', () => {
  const db = openDb(':memory:');
  const first = createWorkspace(db, { id: 'workspace-a', name: 'A' });
  const second = createWorkspace(db, { id: 'workspace-b', name: 'B' });

  const { message } = first.ingestMessage({
    channelId: 'channel-a',
    slackTs: '1000.0001',
    authorId: 'member-a',
    text: 'Please ship the report',
    permalink: 'https://slack.example/messages/1',
  });
  const result = first.upsertDraft({
    sourceMessageId: message.id,
    title: 'Ship the report',
    outcome: 'Report shipped',
    sourcePermalink: message.permalink,
    promptVersion: 'v1',
    confidence: 92,
  });

  assert.equal(result.created, true);
  assert.equal(result.draft.workspaceId, 'workspace-a');
  assert.equal(result.draft.proposedOwnerId, null);
  assert.equal(result.draft.dueDate, null);
  assert.equal(result.draft.trackerTaskId, null);
  assert.equal(second.listDrafts().length, 0);
  assert.equal(first.upsertDraft({
    sourceMessageId: message.id,
    title: 'Duplicate',
    outcome: 'Duplicate',
    sourcePermalink: message.permalink,
    promptVersion: 'v1',
    confidence: 1,
  }).created, false);
});
