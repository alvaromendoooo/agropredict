import { env } from '$env/dynamic/private';

/** Base URL of the data-service API. */
export const DATA_SERVICE_URL = env.DATA_SERVICE_URL ?? 'http://localhost:9002';
/** Base URL of the climate risks predictor API. */
export const PREDICTOR_URL = env.PREDICTOR_URL ?? 'http://localhost:10000';
/** Default outbound request timeout in milliseconds. */
export const REQUEST_TIMEOUT_MS = Number(env.REQUEST_TIMEOUT_MS ?? 45000);
