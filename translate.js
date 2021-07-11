#! /usr/bin/env node

const translate = require('@vitalets/google-translate-api');

translate(process.argv[2], { from: "ko", to: 'en' }).then(res => {
    console.log(res.text);
}).catch(err => {
    console.error(err);
});