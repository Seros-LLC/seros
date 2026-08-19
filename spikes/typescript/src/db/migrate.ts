import { openDb } from './client.ts';
import { config } from '../config.ts';

openDb(config.dbPath);
console.log(JSON.stringify({ level: 'info', event: 'migrate.done', db: config.dbPath }));
