# frozen_string_literal: true

module PhoneNormalizable
  COUNTRY_CODE_LENGTHS = {
    "1" => [ 10 ],
    "7" => [ 10 ],
    "20" => [ 10 ],
    "27" => [ 9 ],
    "30" => [ 10 ],
    "31" => [ 9 ],
    "32" => [ 8, 9 ],
    "33" => [ 9 ],
    "34" => [ 9 ],
    "36" => [ 8, 9 ],
    "39" => [ 9, 10 ],
    "40" => [ 9 ],
    "41" => [ 9 ],
    "43" => [ 10, 11 ],
    "44" => [ 10 ],
    "45" => [ 8 ],
    "46" => [ 9 ],
    "47" => [ 8 ],
    "48" => [ 9 ],
    "49" => [ 10, 11 ],
    "51" => [ 8, 9 ],
    "52" => [ 10 ],
    "53" => [ 8 ],
    "54" => [ 10, 11 ],
    "55" => [ 10, 11 ],
    "56" => [ 9 ],
    "57" => [ 10 ],
    "58" => [ 10 ],
    "60" => [ 9, 10 ],
    "61" => [ 9 ],
    "62" => [ 9, 10, 11, 12 ],
    "63" => [ 10 ],
    "64" => [ 8, 9 ],
    "65" => [ 8 ],
    "66" => [ 9 ],
    "81" => [ 10, 11 ],
    "82" => [ 9, 10 ],
    "84" => [ 9, 10 ],
    "86" => [ 11 ],
    "90" => [ 10 ],
    "91" => [ 10 ],
    "92" => [ 10 ],
    "93" => [ 9 ],
    "94" => [ 9 ],
    "95" => [ 9 ],
    "98" => [ 10 ],
    "212" => [ 9 ],
    "213" => [ 9 ],
    "216" => [ 8 ],
    "220" => [ 7 ],
    "234" => [ 10 ],
    "240" => [ 9 ],
    "244" => [ 9 ],
    "245" => [ 7 ],
    "249" => [ 9 ],
    "254" => [ 9 ],
    "255" => [ 9 ],
    "256" => [ 9 ],
    "258" => [ 9 ],
    "260" => [ 9 ],
    "263" => [ 9 ],
    "351" => [ 9 ],
    "353" => [ 9 ],
    "354" => [ 7 ],
    "358" => [ 9, 10 ],
    "380" => [ 9 ],
    "420" => [ 9 ],
    "852" => [ 8 ],
    "855" => [ 8, 9 ],
    "880" => [ 10 ],
    "886" => [ 9 ],
    "966" => [ 9 ],
    "971" => [ 9 ],
    "972" => [ 9 ]
  }.freeze

  def normalize_phone(phone)
    PhoneNormalizable.normalize_phone(phone)
  end

  def self.normalize_phone(phone)
    return nil if phone.blank?

    digits = phone.to_s.gsub(/\D/, "")
    return nil if digits.empty?

    return digits if valid_country_code?(digits)

    brazilian_length = digits.length.between?(10, 11)
    "55#{digits}" if brazilian_length
  end

  def self.valid_country_code?(digits)
    (1..3).each do |len|
      break if len > digits.length

      prefix = digits[0, len]
      national_lengths = COUNTRY_CODE_LENGTHS[prefix]
      next unless national_lengths

      national_part = digits[len..]
      return true if national_lengths.include?(national_part.length)
    end

    false
  end
end
