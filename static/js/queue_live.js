/**
 * SIH26032: Live Queue Auto-Refresh & Visual Sync
 */

function pollQueueUpdates(centerId, currentToken) {
    if (!centerId) return;
    
    setInterval(function() {
        fetch(`/api/queue_status?center_id=${centerId}&token=${currentToken || ''}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const waitBadge = document.getElementById('live_wait_time');
                    const peopleAheadBadge = document.getElementById('live_people_ahead');
                    const currentCallingBadge = document.getElementById('live_calling_token');
                    
                    if (waitBadge && data.estimated_wait_mins !== undefined) {
                        waitBadge.innerText = `${data.estimated_wait_mins} mins`;
                    }
                    if (peopleAheadBadge && data.people_ahead !== undefined) {
                        peopleAheadBadge.innerText = data.people_ahead;
                    }
                    if (currentCallingBadge && data.calling_token) {
                        currentCallingBadge.innerText = data.calling_token;
                    }
                }
            })
            .catch(err => console.log('Queue polling status:', err));
    }, 10000);
}
