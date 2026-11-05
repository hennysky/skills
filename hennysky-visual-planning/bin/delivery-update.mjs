import { checkForUpdate } from '../scripts/check-update.mjs';

/** Independent local distribution. Generation never calls a remote updater. */
export function startDeliveryUpdateCheck() {
  return checkForUpdate();
}
