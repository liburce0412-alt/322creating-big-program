// utils.js - helper functions
function formatDate(d) { return d.toISOString().split('T')[0]; }
function formatTime(ms) { let m=Math.floor(ms/60); let s=ms%60; return (m<10?'0':'')+m+':'+(s<10?'0':'')+s; }
function sleep(ms) { return new Promise(r=>setTimeout(r,ms)); }
function getQueryParam(name) { return new URLSearchParams(window.location.search).get(name); }
