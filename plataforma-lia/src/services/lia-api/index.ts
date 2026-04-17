export * from './types'

export * from './chat-api'
export * from './candidates-api'
export * from './jobs-api'
export * from './wsi-api'
export * from './misc-api'
export * from './email-api'
export * from './bulk-api'
export * from './notifications-api'
export * from './voice-api'
export * from './feedback-api'
export * from './autonomous-api'

export {
  BACKEND_URL,
  getAuthHeaders,
  getAuthHeadersForFormData,
  fetchWithRetry,
  HttpError,
  parseRetryAfterMs,
} from './base'

import * as chatApi from './chat-api'
import * as candidatesApi from './candidates-api'
import * as jobsApi from './jobs-api'
import * as wsiApi from './wsi-api'
import * as miscApi from './misc-api'
import * as emailApi from './email-api'
import * as bulkApi from './bulk-api'
import * as notificationsApi from './notifications-api'
import * as voiceApi from './voice-api'
import * as feedbackApi from './feedback-api'
import * as autonomousApi from './autonomous-api'

export const liaApi = {
  ...chatApi,
  ...candidatesApi,
  ...jobsApi,
  ...wsiApi,
  ...miscApi,
  ...emailApi,
  ...bulkApi,
  ...notificationsApi,
  ...voiceApi,
  ...feedbackApi,
  ...autonomousApi,
}

export default liaApi
