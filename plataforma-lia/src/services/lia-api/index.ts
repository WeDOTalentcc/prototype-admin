export * from './types'

export * from './chat-api'
export * from './candidates-api'
export * from './jobs-api'
export * from './wsi-api'
export * from './misc-api'
export * from './voice-api'
export * from './feedback-api'
export * from './autonomous-api'

export { BACKEND_URL, getAccessToken, getAuthHeaders, getAuthHeadersForFormData } from './base'

import * as chatApi from './chat-api'
import * as candidatesApi from './candidates-api'
import * as jobsApi from './jobs-api'
import * as wsiApi from './wsi-api'
import * as miscApi from './misc-api'
import * as voiceApi from './voice-api'
import * as feedbackApi from './feedback-api'
import * as autonomousApi from './autonomous-api'

export const liaApi = {
  ...chatApi,
  ...candidatesApi,
  ...jobsApi,
  ...wsiApi,
  ...miscApi,
  ...voiceApi,
  ...feedbackApi,
  ...autonomousApi,
}

export default liaApi
