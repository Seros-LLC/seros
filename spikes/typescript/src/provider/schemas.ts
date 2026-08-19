import { z } from 'zod';

/** Pass A: cheap-tier detection over a batch of messages. */
export const DetectionSchema = z.object({
  results: z.array(z.object({
    ref: z.string(),
    isCommitment: z.boolean(),
    confidence: z.number().int().min(0).max(100),
    reason: z.string().max(120),
  })).min(1),
});
export type Detection = z.infer<typeof DetectionSchema>;

/** Pass B: standard-tier drafting for a survivor. */
export const DraftSchema = z.object({
  title: z.string().min(3).max(120),
  outcome: z.string().min(3).max(300),
  proposedOwner: z.string().nullable(),
  dueDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable(),
  confidence: z.number().int().min(0).max(100),
});
export type Draft = z.infer<typeof DraftSchema>;
