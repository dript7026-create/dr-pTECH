# Short-Notice Deployment Checklist

Prepared for the current review snapshot.

Use this when a client review window opens with little warning.

## T-60 minutes

1. Re-run the validated package build script.
2. Run the same script once with `-PreflightOnly` if you want a fast fail before rebuilding.
3. Confirm the review zip rebuilds successfully.
4. Confirm the `external_client_review_latest.zip` alias is refreshed.
5. Confirm the Android review APK rebuilds successfully.
6. Check artifact timestamps and sizes.

## T-45 minutes

1. Open the product brief and executive summary for wording review.
2. Confirm the validation snapshot still reflects the intended review scope.
3. Ensure Pertinence is described as the scaled example, not the product.
4. Read `HANDOFF_NOTE.md` and confirm its artifact paths match the rebuilt package.

## T-30 minutes

1. Install the APK on a device or emulator if available.
2. Open each in-app document once to confirm asset sync.
3. Confirm the zip opens and top-level files are present.
4. If an Android phone is connected, run `egosphere\tools\install_review_app_to_phone.ps1`.

## T-15 minutes

1. Decide which artifact leads the conversation:
   - executive summary for non-technical stakeholders;
   - product brief for mixed audiences;
   - client presentation script for live delivery;
   - review guide for technical deep dive.
2. Have the latest zip and APK paths ready.
3. Prefer the stable `external_client_review_latest.zip` path if the dated archive name could create confusion.
4. Have a plain-language explanation ready for what is validated versus what is future-facing.

## T-5 minutes

1. Verify the final artifact paths one more time.
2. Close unrelated windows and terminals.
3. Keep one fallback sentence ready:
   - the APK is a review companion and the zip is the validated technical package.

## After the meeting

1. Record what the client focused on.
2. Update the package wording if they misunderstood the product boundary.
3. Rebuild again only if source or validation state changed.
