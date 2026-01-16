# GitHub Actions Heartbeat Setup

## What This Does
The GitHub Actions workflow automatically pings your heartbeat endpoint every 5 minutes, keeping your Render app active 24/7.

## File Location
`.github/workflows/heartbeat.yml`

## How to Enable

### Step 1: Commit and Push
```bash
git add .github/workflows/heartbeat.yml
git commit -m "Add GitHub Actions heartbeat workflow"
git push origin main
```

### Step 2: Enable Actions (if not already enabled)
1. Go to your GitHub repository
2. Click **Actions** tab
3. If you see "Workflows aren't being run on this repository", click **Enable GitHub Actions**

### Step 3: Verify It's Running
1. Go to **Actions** tab in GitHub
2. Look for "Heartbeat - Keep App Active" workflow
3. You should see it scheduled to run every 5 minutes

## Manual Testing

### Trigger Manually
1. Go to **Actions** tab
2. Click **Heartbeat - Keep App Active**
3. Click **Run workflow** button
4. Select **main** branch
5. Click **Run workflow**

### Check Logs
1. Click on the workflow run
2. Click on the **heartbeat** job
3. Expand **Ping heartbeat endpoint** step to see the response

## Expected Output
```
Status: 200
```

If you see 200, the heartbeat is working!

## Troubleshooting

### Workflow Not Running
- Make sure GitHub Actions is enabled in your repository
- Check that the `.github/workflows/heartbeat.yml` file is in the main branch
- Wait a few minutes - GitHub Actions can take time to schedule

### Getting 405 Errors
- Your Render app hasn't been deployed with the latest heartbeat fix
- Deploy your changes to Render first
- Then the workflow will get 200 OK

### Getting Connection Refused
- Your Render app might be down
- Check Render dashboard for any errors
- Verify the URL is correct

## Advantages of GitHub Actions
✅ Free - included with GitHub  
✅ Reliable - GitHub's infrastructure  
✅ No external services needed  
✅ Easy to monitor and debug  
✅ Can be triggered manually anytime  

## Disabling the Workflow
If you want to stop the heartbeat:
1. Go to **Actions** tab
2. Click **Heartbeat - Keep App Active**
3. Click the **...** menu
4. Click **Disable workflow**

## Re-enabling the Workflow
1. Go to **Actions** tab
2. Click **Heartbeat - Keep App Active**
3. Click the **...** menu
4. Click **Enable workflow**

## Notes
- The workflow runs on GitHub's free runners
- Each run takes about 10-15 seconds
- You can see all runs in the Actions history
- The workflow includes verbose output for debugging
