/**
 * Video UI Interactions
 * Handles drag-and-drop and toggle view functionality for video call interface
 */

// ========================================
// Video View Toggle
// ========================================

// View state - track which video is in main view
let isLocalInMainView = false; // false = remote in main, true = local in main

/**
 * Toggle view - swap between local and remote video
 * @param {Object} localTracks - Object containing local audio and video tracks
 * @param {Object} remoteUsers - Object containing remote user data
 * @param {HTMLElement} mainVideo - Main video container element
 * @param {HTMLElement} selfView - Self view container element
 */
function toggleVideoView(localTracks, remoteUsers, mainVideo, selfView) {
    // Get the first remote user
    const remoteUser = Object.values(remoteUsers)[0];

    // Only allow toggle if we have both local and remote tracks
    if (!localTracks.videoTrack || !remoteUser || !remoteUser.videoTrack) {
        console.log('Cannot toggle view - missing video tracks');
        return;
    }

    // Clear both containers
    mainVideo.innerHTML = '';
    selfView.innerHTML = '';

    if (isLocalInMainView) {
        // Switch back: Local to small view, Remote to main view
        localTracks.videoTrack.play(selfView);
        remoteUser.videoTrack.play(mainVideo);

        // Update labels
        const selfLabel = document.createElement('div');
        selfLabel.id = 'self-name';
        selfLabel.className = 'absolute bottom-2 left-2 bg-black/60 text-white px-2 py-1 rounded text-xs pointer-events-none';
        selfLabel.textContent = 'You';
        selfView.appendChild(selfLabel);

        const remoteLabel = document.createElement('div');
        remoteLabel.id = 'remote-name';
        remoteLabel.className = 'absolute bottom-4 left-4 bg-black/60 text-white px-3 py-1 rounded text-sm pointer-events-none';
        remoteLabel.textContent = `Participant ${remoteUser.uid}`;
        mainVideo.appendChild(remoteLabel);

        isLocalInMainView = false;
        console.log('Switched to remote in main view');
    } else {
        // Switch: Local to main view, Remote to small view
        localTracks.videoTrack.play(mainVideo);
        remoteUser.videoTrack.play(selfView);

        // Update labels
        const mainLabel = document.createElement('div');
        mainLabel.id = 'remote-name';
        mainLabel.className = 'absolute bottom-4 left-4 bg-black/60 text-white px-3 py-1 rounded text-sm pointer-events-none';
        mainLabel.textContent = 'You';
        mainVideo.appendChild(mainLabel);

        const smallLabel = document.createElement('div');
        smallLabel.id = 'self-name';
        smallLabel.className = 'absolute bottom-2 left-2 bg-black/60 text-white px-2 py-1 rounded text-xs pointer-events-none';
        smallLabel.textContent = `Participant ${remoteUser.uid}`;
        selfView.appendChild(smallLabel);

        isLocalInMainView = true;
        console.log('Switched to local in main view');
    }
}

/**
 * Reset view state (call when leaving a call)
 */
function resetViewState() {
    isLocalInMainView = false;
}

// ========================================
// Drag and Drop Self-View with Snap-to-Corner
// ========================================

// Drag state
let isDragging = false;
let hasDragged = false; // Track if user actually dragged (vs just clicked)
let dragStartX = 0;
let dragStartY = 0;
let selfViewStartX = 0;
let selfViewStartY = 0;

// Corner positions configuration
const PADDING = 16; // Distance from edges (matches Tailwind's spacing)
const BOTTOM_BAR_HEIGHT = 80; // Height of control bar (20 in Tailwind units = 80px)
const CORNER_MARGIN = 16; // Additional margin for bottom corners

/**
 * Get corner positions based on viewport
 * @param {HTMLElement} selfView - Self view element
 * @returns {Object} Corner positions
 */
function getCornerPositions(selfView) {
    const rect = selfView.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    return {
        'bottom-right': {
            bottom: BOTTOM_BAR_HEIGHT + CORNER_MARGIN,
            right: PADDING,
            top: null,
            left: null
        },
        'bottom-left': {
            bottom: BOTTOM_BAR_HEIGHT + CORNER_MARGIN,
            left: PADDING,
            top: null,
            right: null
        },
        'top-right': {
            top: PADDING,
            right: PADDING,
            bottom: null,
            left: null
        },
        'top-left': {
            top: PADDING,
            left: PADDING,
            bottom: null,
            right: null
        }
    };
}

/**
 * Find nearest corner based on current position
 * @param {number} x - X position
 * @param {number} y - Y position
 * @param {HTMLElement} selfView - Self view element
 * @returns {string} Corner name
 */
function findNearestCorner(x, y, selfView) {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const rect = selfView.getBoundingClientRect();

    // Calculate center point of the element
    const centerX = x + rect.width / 2;
    const centerY = y + rect.height / 2;

    // Determine which quadrant the center is in
    const isRight = centerX > viewportWidth / 2;
    const isBottom = centerY > viewportHeight / 2;

    if (isBottom && isRight) return 'bottom-right';
    if (isBottom && !isRight) return 'bottom-left';
    if (!isBottom && isRight) return 'top-right';
    return 'top-left';
}

/**
 * Apply corner position to self-view
 * @param {string} corner - Corner name
 * @param {HTMLElement} selfView - Self view element
 */
function snapToCorner(corner, selfView) {
    const positions = getCornerPositions(selfView);
    const pos = positions[corner];

    // Remove all position classes
    selfView.style.top = '';
    selfView.style.bottom = '';
    selfView.style.left = '';
    selfView.style.right = '';

    // Apply new position
    if (pos.top !== null) selfView.style.top = `${pos.top}px`;
    if (pos.bottom !== null) selfView.style.bottom = `${pos.bottom}px`;
    if (pos.left !== null) selfView.style.left = `${pos.left}px`;
    if (pos.right !== null) selfView.style.right = `${pos.right}px`;

    // Save preference to localStorage
    localStorage.setItem('selfViewCorner', corner);
    console.log(`Self-view snapped to: ${corner}`);
}

/**
 * Initialize drag and drop functionality
 * @param {HTMLElement} selfView - Self view element
 * @param {HTMLElement} mainVideo - Main video element
 * @param {Function} onToggle - Callback for toggle view
 */
function initializeDragAndDrop(selfView, mainVideo, onToggle) {
    // Mouse down - start dragging
    selfView.addEventListener('mousedown', (e) => {
        isDragging = true;
        hasDragged = false;

        const rect = selfView.getBoundingClientRect();
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        selfViewStartX = rect.left;
        selfViewStartY = rect.top;

        // Remove transition during drag for smooth movement
        selfView.style.transition = 'none';

        // Prevent text selection while dragging
        e.preventDefault();
    });

    // Mouse move - drag the element
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;

        const deltaX = e.clientX - dragStartX;
        const deltaY = e.clientY - dragStartY;

        // If moved more than 5px, consider it a drag (not a click)
        if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
            hasDragged = true;
        }

        const newX = selfViewStartX + deltaX;
        const newY = selfViewStartY + deltaY;

        // Apply position
        selfView.style.top = `${newY}px`;
        selfView.style.bottom = 'auto';
        selfView.style.left = `${newX}px`;
        selfView.style.right = 'auto';
    });

    // Mouse up - snap to nearest corner or toggle view if clicked
    document.addEventListener('mouseup', (e) => {
        if (!isDragging) return;

        isDragging = false;

        // Re-enable transition for smooth snap
        selfView.style.transition = 'all 0.2s';

        if (hasDragged) {
            // User dragged - snap to corner
            const rect = selfView.getBoundingClientRect();
            const nearestCorner = findNearestCorner(rect.left, rect.top, selfView);
            snapToCorner(nearestCorner, selfView);
        } else {
            // User clicked - toggle view
            onToggle();
        }
    });

    // Touch support for mobile
    selfView.addEventListener('touchstart', (e) => {
        isDragging = true;
        hasDragged = false;

        const touch = e.touches[0];
        const rect = selfView.getBoundingClientRect();

        dragStartX = touch.clientX;
        dragStartY = touch.clientY;
        selfViewStartX = rect.left;
        selfViewStartY = rect.top;

        selfView.style.transition = 'none';
        e.preventDefault();
    });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;

        const touch = e.touches[0];
        const deltaX = touch.clientX - dragStartX;
        const deltaY = touch.clientY - dragStartY;

        // If moved more than 5px, consider it a drag (not a tap)
        if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
            hasDragged = true;
        }

        const newX = selfViewStartX + deltaX;
        const newY = selfViewStartY + deltaY;

        selfView.style.top = `${newY}px`;
        selfView.style.bottom = 'auto';
        selfView.style.left = `${newX}px`;
        selfView.style.right = 'auto';
    });

    document.addEventListener('touchend', (e) => {
        if (!isDragging) return;

        isDragging = false;
        selfView.style.transition = 'all 0.2s';

        if (hasDragged) {
            // User dragged - snap to corner
            const rect = selfView.getBoundingClientRect();
            const nearestCorner = findNearestCorner(rect.left, rect.top, selfView);
            snapToCorner(nearestCorner, selfView);
        } else {
            // User tapped - toggle view
            onToggle();
        }
    });

    // Click handler for main video - toggle view
    mainVideo.addEventListener('click', (e) => {
        // Only toggle if clicking on the video container (not during drag)
        if (!isDragging) {
            onToggle();
        }
    });

    // Load saved position on page load
    window.addEventListener('DOMContentLoaded', () => {
        const savedCorner = localStorage.getItem('selfViewCorner') || 'bottom-right';
        snapToCorner(savedCorner, selfView);
    });

    // Reposition on window resize
    window.addEventListener('resize', () => {
        const savedCorner = localStorage.getItem('selfViewCorner') || 'bottom-right';
        snapToCorner(savedCorner, selfView);
    });
}
